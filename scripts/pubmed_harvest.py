#!/usr/bin/env python3
"""Harvest PubMed → state.sqlite + 90-Sorgenti/abstract/.

Idempotente: un PMID già presente non viene sovrascritto, viene solo aggiunta
la query che lo ha intercettato e aggiornata la data di ultimo aggiornamento.

Uso:
    python3 scripts/pubmed_harvest.py --all
    python3 scripts/pubmed_harvest.py --all --dry-run
    python3 scripts/pubmed_harvest.py --query Q1-head-to-head Q4-fosfato-fgf23
    python3 scripts/pubmed_harvest.py --all --priorita 1
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import date

import requests

from common import (
    DIR_ABSTRACT, IN_WIKI, LIMITE_DATA_RE, LOG_DIR, NCBI_API_KEY, NCBI_EMAIL,
    NCBI_TOOL, USER_AGENT, build_term, connect, corpus_query, init_db,
    load_queries, log_run, ncbi_limiter, now_iso, query_spec, require_env,
    senza_finestra, unisci_corpus,
)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BATCH = 200


def _base_params() -> dict:
    p = {"db": "pubmed", "tool": NCBI_TOOL, "email": NCBI_EMAIL}
    if NCBI_API_KEY:
        p["api_key"] = NCBI_API_KEY
    return p


def _get(path: str, params: dict, tries: int = 4) -> requests.Response:
    """POST anziché GET: i term di queries.yaml superano il kilobyte e NCBI
    raccomanda POST oltre i ~2000 caratteri di URL."""
    last = None
    for attempt in range(tries):
        ncbi_limiter.wait()
        try:
            r = requests.post(
                f"{EUTILS}/{path}", data=params,
                headers={"User-Agent": USER_AGENT}, timeout=90,
            )
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = 2 ** attempt
            print(f"  ! {path} tentativo {attempt + 1}/{tries} fallito ({exc}); "
                  f"ritento fra {wait}s", file=sys.stderr)
            import time as _t
            _t.sleep(wait)
    raise RuntimeError(f"{path} fallito dopo {tries} tentativi: {last}")


def esearch(term: str) -> tuple[int, str, str, str]:
    """Ritorna (count, webenv, query_key, querytranslation) usando la History
    Server."""
    p = _base_params() | {
        "term": term, "retmode": "json", "retmax": 0, "usehistory": "y",
    }
    data = _get("esearch.fcgi", p).json()["esearchresult"]
    if "ERROR" in data:
        raise RuntimeError(f"PubMed ha rifiutato la query: {data['ERROR']}")
    return (int(data["count"]), data.get("webenv", ""), data.get("querykey", ""),
            data.get("querytranslation", ""))


def efetch(webenv: str, query_key: str, start: int, n: int) -> ET.Element:
    p = _base_params() | {
        "WebEnv": webenv, "query_key": query_key, "retmode": "xml",
        "retstart": start, "retmax": n,
    }
    return ET.fromstring(_get("efetch.fcgi", p).content)


# ------------------------------------------------------------------- parsing XML
def _text(node, path: str, default: str = "") -> str:
    el = node.find(path)
    if el is None:
        return default
    return " ".join("".join(el.itertext()).split())


def parse_article(art: ET.Element) -> dict | None:
    cit = art.find("MedlineCitation")
    if cit is None:
        return None
    pmid = _text(cit, "PMID")
    if not pmid:
        return None
    a = cit.find("Article")
    if a is None:
        return None

    doi = pmcid = ""
    for aid in art.iterfind("PubmedData/ArticleIdList/ArticleId"):
        t = aid.get("IdType")
        if t == "doi" and aid.text:
            doi = aid.text.strip()
        elif t == "pmc" and aid.text:
            pmcid = aid.text.strip()

    autori = []
    for au in a.iterfind("AuthorList/Author"):
        ln, ini = _text(au, "LastName"), _text(au, "Initials")
        if ln:
            autori.append(f"{ln} {ini}".strip())
        elif _text(au, "CollectiveName"):
            autori.append(_text(au, "CollectiveName"))
    if len(autori) > 3:
        autori_str = f"{autori[0]}, et al."
    else:
        autori_str = ", ".join(autori)

    anno = ""
    for path in ("Journal/JournalIssue/PubDate/Year",
                 "Journal/JournalIssue/PubDate/MedlineDate"):
        raw = _text(a, path)
        if raw:
            anno = raw[:4]
            break
    if not anno:
        anno = _text(art, "PubmedData/History/PubMedPubDate/Year")

    # Abstract strutturato: conserva le etichette, servono all'estrazione dati.
    parti = []
    for ab in a.iterfind("Abstract/AbstractText"):
        label = (ab.get("Label") or "").strip()
        body = " ".join("".join(ab.itertext()).split())
        parti.append(f"**{label}:** {body}" if label else body)

    pubtypes = [_text(pt, ".") for pt in a.iterfind("PublicationTypeList/PublicationType")]

    return {
        "pmid": pmid,
        "doi": doi,
        "pmcid": pmcid,
        "titolo": _text(a, "ArticleTitle"),
        "autori": autori_str,
        "anno": int(anno) if anno.isdigit() else None,
        "rivista": _text(a, "Journal/ISOAbbreviation") or _text(a, "Journal/Title"),
        "pubtypes": "; ".join(pubtypes),
        "lingua": _text(a, "Language"),
        "abstract": "\n\n".join(parti),
    }


# ----------------------------------------------------------------------- scrittura
ABSTRACT_TMPL = """---
tipo: sorgente-abstract
pmid: "{pmid}"
doi: "{doi}"
pmcid: "{pmcid}"
anno: {anno}
rivista: "{rivista}"
pubtypes: "{pubtypes}"
---

# {titolo}

{autori} — *{rivista}* ({anno})

- PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/
{doi_line}
## Abstract

{abstract}
"""


def write_abstract(rec: dict) -> None:
    DIR_ABSTRACT.mkdir(parents=True, exist_ok=True)
    doi_line = f"- DOI: https://doi.org/{rec['doi']}\n" if rec["doi"] else ""
    body = ABSTRACT_TMPL.format(
        **{**rec,
           "anno": rec["anno"] or "",
           "titolo": rec["titolo"] or "(senza titolo)",
           "abstract": rec["abstract"] or "_Abstract non disponibile in PubMed._",
           "doi_line": doi_line,
           "rivista": (rec["rivista"] or "").replace('"', "'")}
    )
    (DIR_ABSTRACT / f"{rec['pmid']}.md").write_text(body, encoding="utf-8")


def upsert(con, rec: dict, query_name: str, corpus: str) -> str:
    """`corpus` è quello della query ('wiki' o 'meta'): si somma a quello già
    registrato, non lo sostituisce. «nuovo» vuol dire nuovo per quel corpus: un
    record già noto alla sola meta-analisi che entra nel wiki è nuovo per il
    wiki e va in coda di screening."""
    cur = con.execute("SELECT corpus FROM record WHERE pmid = ?", (rec["pmid"],))
    riga = cur.fetchone()
    esiste = riga is not None
    nel_corpus = esiste and corpus in riga["corpus"].split("+")
    if esiste:
        con.execute(
            """UPDATE record SET doi=COALESCE(NULLIF(?,''), doi),
                                 pmcid=COALESCE(NULLIF(?,''), pmcid),
                                 corpus=?,
                                 ultimo_aggiornamento=?
               WHERE pmid=?""",
            (rec["doi"], rec["pmcid"], unisci_corpus(riga["corpus"], corpus),
             now_iso(), rec["pmid"]),
        )
    else:
        con.execute(
            """INSERT INTO record (pmid, doi, pmcid, titolo, autori, anno, rivista,
                                   pubtypes, lingua, abstract, primo_harvest,
                                   ultimo_aggiornamento, corpus)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rec["pmid"], rec["doi"], rec["pmcid"], rec["titolo"], rec["autori"],
             rec["anno"], rec["rivista"], rec["pubtypes"], rec["lingua"],
             rec["abstract"], now_iso(), now_iso(), corpus),
        )
        write_abstract(rec)
    con.execute("INSERT OR IGNORE INTO record_query (pmid, query) VALUES (?,?)",
                (rec["pmid"], query_name))
    return "aggiornato" if nel_corpus else "nuovo"


# --------------------------------------------------------------------------- main
def harvest(name: str, cfg: dict, dry_run: bool) -> tuple[int, int]:
    term = build_term(name, cfg)
    count, webenv, qkey, traduzione = esearch(term)
    print(f"\n[{name}] {count} record")
    if senza_finestra(query_spec(name, cfg)):
        # Controllo bloccante del protocollo di meta-analisi, §7.1: PubMed non
        # deve aver applicato alcun limite di data.
        trovato = LIMITE_DATA_RE.search(traduzione)
        if trovato:
            raise RuntimeError(f"{name}: la querytranslation contiene un limite di "
                               f"data ({trovato.group(0)}); ricerca invalida")
        print("  controllo §7.1: nessun limite di data nella querytranslation")
        dest = LOG_DIR / f"querytranslation-{name}-{date.today():%Y-%m-%d}.txt"
        dest.write_text(f"# {now_iso()} — {count} record\n\n## term\n{term}\n\n"
                        f"## querytranslation\n{traduzione}\n", encoding="utf-8")
        print(f"  querytranslation salvata in {dest.relative_to(LOG_DIR.parent.parent)}")
    if dry_run or count == 0:
        if dry_run:
            print(f"  term: {term}")
            print(f"  querytranslation: {traduzione}")
        return count, 0

    corpus = corpus_query(name, cfg)
    con = connect()
    nuovi = 0
    libri: list[str] = []
    try:
        for start in range(0, count, BATCH):
            root = efetch(webenv, qkey, start, BATCH)
            for art in root.iterfind("PubmedArticle"):
                rec = parse_article(art)
                if rec and upsert(con, rec, name, corpus) == "nuovo":
                    nuovi += 1
            # Libri e rapporti (es. HTA CADTH) non sono importati, ma non devono
            # sparire in silenzio: contano fra i record identificati (PRISMA).
            for book in root.iterfind("PubmedBookArticle"):
                libri.append(_text(book, "BookDocument/PMID"))
            con.commit()
            print(f"  … {min(start + BATCH, count)}/{count}", flush=True)
    finally:
        con.commit()
        con.close()
    if libri:
        print(f"  ! {len(libri)} libri/rapporti (PubmedBookArticle) NON importati: "
              f"{', '.join(libri)}")
        log_run("pubmed_harvest", name, "libri-non-importati", ", ".join(libri))
    print(f"  → {nuovi} nuovi, {count - nuovi - len(libri)} già presenti")
    return count, nuovi


def main() -> None:
    ap = argparse.ArgumentParser(description="Harvest PubMed per FDI-FCM-Wiki")
    ap.add_argument("--all", action="store_true", help="esegue tutte le query")
    ap.add_argument("--query", nargs="+", metavar="NOME", help="query specifiche")
    ap.add_argument("--priorita", type=int, help="limita alla priorità indicata o superiore")
    ap.add_argument("--dry-run", action="store_true", help="solo conteggi, non scrive")
    args = ap.parse_args()

    if not args.all and not args.query:
        ap.error("specifica --all oppure --query NOME [NOME ...]")

    require_env("NCBI_EMAIL")
    if not NCBI_API_KEY:
        print("AVVISO: NCBI_API_KEY non impostata, rate limit a 3 req/s.", file=sys.stderr)

    init_db()
    cfg = load_queries()
    # --all esegue solo le query del wiki: quelle di query_meta alimentano il
    # corpus della meta-analisi e si chiamano per nome.
    nomi = args.query or list(cfg["query"])
    meta = cfg.get("query_meta") or {}
    ignoti = [n for n in nomi if n not in cfg["query"] and n not in meta]
    if ignoti:
        ap.error(f"query non definite in queries.yaml: {', '.join(ignoti)}")
    if args.priorita:
        nomi = [n for n in nomi if query_spec(n, cfg).get("priorita", 9) <= args.priorita]

    tot_nuovi = tot_record = 0
    for nome in nomi:
        c, n = harvest(nome, cfg, args.dry_run)
        tot_record += c
        tot_nuovi += n

    if args.dry_run:
        # In dry-run non si scaricano i PMID, quindi i nuovi non si possono contare:
        # stampare «0 nuovi» farebbe credere che il corpus sia gia completo.
        print(f"\nDRY RUN — {tot_record} hit complessivi (con sovrapposizioni); "
              "record nuovi non calcolati in dry-run")
    else:
        print(f"\n{tot_record} hit complessivi (con sovrapposizioni), {tot_nuovi} record nuovi")
    if not args.dry_run:
        con = connect()
        distinti = con.execute(f"SELECT COUNT(*) FROM record WHERE {IN_WIKI}").fetchone()[0]
        n_meta = con.execute("SELECT COUNT(*) FROM record WHERE corpus != 'wiki'").fetchone()[0]
        con.close()
        print(f"Corpus del wiki: {distinti} record distinti; corpus meta: {n_meta}")
        log_run("pubmed_harvest", ",".join(nomi), "ok",
                f"{tot_nuovi} nuovi, corpus {distinti}")


if __name__ == "__main__":
    main()
