#!/usr/bin/env python3
"""Importa gli export delle ricerche manuali della meta-analisi (protocollo §7;
istruzioni per l'utente in 99-Meta/ricerca-manuale-meta.md).

    python3 scripts/export_meta.py --embase  99-Meta/log/export-ricerca/embase-AAAA-MM-GG.ris --dry-run
    python3 scripts/export_meta.py --central 99-Meta/log/export-ricerca/central-AAAA-MM-GG.ris
    python3 scripts/export_meta.py --ictrp   99-Meta/log/export-ricerca/ictrp-AAAA-MM-GG.xml
    python3 scripts/export_meta.py --ictrp   ictrp-fdi-….xml ictrp-fcm-….xml   # intersezione

Ogni record dell'export si risolve contro il DB, nell'ordine: PMID, DOI,
identificativo della fonte, numero di registro (solo per i record di registro),
titolo normalizzato. I primi quattro sono duplicati certi: il record esistente
riceve la fonte in record_query (S-embase, S-central, S-ictrp) ed entra nel
corpus meta se era del solo wiki. La coincidenza del solo titolo è un sospetto
(un abstract congressuale e l'articolo che ne deriva hanno spesso lo stesso
titolo): l'import si ferma e li elenca, e si rilancia con

    --titoli duplicati [--eccetto ID,ID]    i sospetti sono duplicati, tranne quelli elencati
    --titoli nuovi     [--eccetto ID,ID]    i sospetti sono record nuovi, tranne quelli elencati

Un record nuovo con PMID entra dal record PubMed (efetch), come nell'harvest;
gli altri entrano con un identificativo proprio nella colonna `pmid`:
EMB-L…, CENTRAL-CN-… (NCT… o EUCTR-… se è un record di registro), NCT…,
EUCTR-…, CTIS-…, ICTRP-…; in mancanza, DOI-… o
<FONTE>-T<hash del titolo>. Conteggi e liste vanno in
99-Meta/log/export-meta-<data>.json; la riga del registro della ricerca
(ma-ricerca-….md) si compila a mano da lì, con il numero mostrato dalla fonte.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from common import LOG_DIR, connect, init_db, now_iso

RIGA_RIS = re.compile(r"^([A-Z][A-Z0-9])  -(?: (.*))?$")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")
NCT_RE = re.compile(r"NCT\d{8}")
EUDRACT_RE = re.compile(r"(?<!\d)(\d{4}-\d{6}-\d{2})(?!\d)")
SIGLE = {"embase": "EMB", "central": "CENTRAL", "ictrp": "ICTRP"}


# ------------------------------------------------------------------ utilità
def leggi(path: str) -> str:
    dati = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return dati.decode(enc)
        except UnicodeDecodeError:
            continue
    return dati.decode("latin-1")


def pulisci(t: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def norma_titolo(t: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", pulisci(t).lower())


def norma_doi(t: str | None) -> str:
    m = DOI_RE.search(t or "")
    return m.group(0).rstrip(".,;)") if m else ""


def id_registro(t: str) -> list[str]:
    """Identificativi di registro nella forma usata dal DB (NCT…, EUCTR-…)."""
    return NCT_RE.findall(t) + [f"EUCTR-{n}" for n in EUDRACT_RE.findall(t)]


def id_di_riserva(fonte: str, doi: str, titolo: str) -> str:
    if doi:
        return "DOI-" + doi.replace("/", "_")
    return f"{SIGLE[fonte]}-T{hashlib.sha1(norma_titolo(titolo).encode()).hexdigest()[:10]}"


# ------------------------------------------------------------------ RIS
def parse_ris(testo: str) -> list[dict[str, list[str]]]:
    """Un dizionario tag → valori per record. Le righe senza tag continuano il
    valore precedente; un record senza ER finale si tiene lo stesso."""
    recs, cur, ultimo = [], {}, None
    for riga in testo.splitlines():
        m = RIGA_RIS.match(riga.rstrip())
        if m:
            tag, val = m.group(1), (m.group(2) or "").strip()
            if tag == "ER":
                if cur:
                    recs.append(cur)
                cur, ultimo = {}, None
            else:
                cur.setdefault(tag, []).append(val)
                ultimo = tag
        elif riga.strip() and ultimo:
            cur[ultimo][-1] += " " + riga.strip()
    if cur:
        recs.append(cur)
    return recs


def da_ris(fonte: str, r: dict[str, list[str]]) -> dict:
    def primo(*tags: str) -> str:
        return next((v for t in tags for v in r.get(t, []) if v), "")

    tutti = [v for vs in r.values() for v in vs]
    titolo = pulisci(primo("T1", "TI"))
    doi = norma_doi(primo("DO")) or next(
        (norma_doi(v) for t in ("UR", "L2", "L3", "LK", "US") for v in r.get(t, [])
         if "doi.org/" in v), "")
    pmid = next((v for v in r.get("C5", []) if v.isdigit()), "")
    if not pmid:
        pmid = next((m.group(1) for v in tutti
                     if (m := re.match(r"PUBMED[ :]+(\d+)$", v.strip(), re.I))), "")
    tipo = "; ".join(r.get("M3", []))
    anno = re.search(r"(?:19|20)\d{2}", primo("PY", "Y1", "DA"))
    rivista = primo("JF", "JO", "T2", "JA", "J2")
    sede = primo("VL")
    if primo("IS"):
        sede += f"({primo('IS')})"
    pagine = "-".join(x for x in (primo("SP"), primo("EP")) if x)
    if pagine:
        sede += f":{pagine}" if sede else pagine
    url = primo("UR", "US", "L2", "LK")

    alias: list[str] = []
    if fonte == "embase":
        acc = next((v for v in r.get("U2", []) + r.get("AN", []) if re.fullmatch(r"L\d+", v)), "")
        ident = f"EMB-{acc}" if acc else id_di_riserva(fonte, doi, titolo)
        link = url or (f"https://www.embase.com/records?subaction=viewrecord&id={acc}" if acc
                       else f"https://doi.org/{doi}" if doi else "")
    else:
        acc = next((v for v in r.get("ID", []) + r.get("AN", []) if re.fullmatch(r"CN-\d+", v)), "")
        ident = f"CENTRAL-{acc}" if acc else id_di_riserva(fonte, doi, titolo)
        link = (f"https://www.cochranelibrary.com/central/doi/10.1002/central/{acc}/full"
                if acc else url or (f"https://doi.org/{doi}" if doi else ""))
        # Solo un record di registro coincide con la registrazione già nel DB:
        # un articolo che cita il proprio NCT è un'altra cosa.
        if "registry" in tipo.lower() or re.search(r"clinicaltrials\.gov|trialsearch\.who|"
                                                   r"clinicaltrialsregister\.eu", url):
            alias = id_registro(" ".join([titolo, url] + r.get("AN", []) + r.get("ID", [])))
    return {
        "id": ident, "pmid_vero": pmid, "doi": doi, "titolo": titolo,
        "autori": "; ".join(r.get("AU", []) or r.get("A1", [])),
        "anno": int(anno.group(0)) if anno else None,
        "rivista": f"{rivista} {sede}".strip(),
        "pubtypes": "; ".join(x for x in (tipo, f"RIS {primo('TY')}" if primo("TY") else "",
                                          f"source {fonte}") if x),
        "abstract": pulisci(primo("N2", "AB")) or f"Abstract non presente nell'export {fonte}.",
        "link": link, "alias": alias,
    }


# ------------------------------------------------------------------ ICTRP
def id_ictrp(trial_id: str) -> str:
    t = trial_id.strip()
    if NCT_RE.fullmatch(t):
        return t
    if t.upper().startswith("EUCTR") and EUDRACT_RE.search(t):
        return f"EUCTR-{EUDRACT_RE.search(t).group(1)}"    # senza suffisso di paese
    if t.upper().startswith("CTIS"):
        return "CTIS-" + t[4:].lstrip("-")
    return "ICTRP-" + re.sub(r"[^A-Za-z0-9.-]", "_", t)


def parse_ictrp(testo: str) -> tuple[int, list[dict]]:
    """Export XML di trialsearch.who.int: un elemento <Trial> per registrazione,
    un sottoelemento per campo. I nomi dei campi si leggono senza distinguere
    maiuscole, perché l'export non è documentato e cambia. Restituisce il
    numero di elementi <Trial> e le registrazioni distinte (l'EU CTR ne ha una
    per paese)."""
    root = ET.fromstring(testo.encode("utf-8"))
    trial = [e for e in root.iter() if e.tag.lower() == "trial"]
    out: dict[str, dict] = {}
    for e in trial:
        c = {x.tag.lower(): pulisci(x.text) for x in e}
        tid = c.get("trialid", "")
        if not tid:
            continue
        ident = id_ictrp(tid)
        if ident in out:          # stesso EudraCT, un record per paese
            continue
        sec = c.get("secondary_id", "") or c.get("secondaryids", "")
        righe = [
            f"Scientific title: {c.get('scientific_title', '')}",
            f"Register: {c.get('source_register', '')}; trial ID {tid}; registered "
            f"{c.get('date_registration', '')}; first enrolment {c.get('date_enrollement', '')}",
            f"Status: {c.get('recruitment_status', '')}; results posted: "
            f"{c.get('results_yes_no', '') or 'non indicato'}; results date "
            f"{c.get('results_date_posted', '') or c.get('results_date_completed', '')}",
            f"Study type: {c.get('study_type', '')}; design: {c.get('study_design', '')}; "
            f"phase: {c.get('phase', '')}; target size: {c.get('target_size', '')}",
            f"Countries: {c.get('countries', '')}",
            f"Eligibility: minimum age {c.get('inclusion_agemin', '')}; maximum age "
            f"{c.get('inclusion_agemax', '')}",
            f"Condition: {c.get('condition', '')}",
            f"Intervention: {c.get('intervention', '')}",
            f"Primary outcome: {c.get('primary_outcome', '')}",
            f"Secondary outcome: {c.get('secondary_outcome', '')}",
            f"Primary sponsor: {c.get('primary_sponsor', '')}",
            f"Secondary IDs: {sec}",
        ]
        anno = re.search(r"(?:19|20)\d{2}", c.get("date_enrollement", "")
                         or c.get("date_registration", ""))
        out[ident] = {
            "id": ident, "pmid_vero": "", "doi": "",
            "titolo": c.get("public_title", "") or c.get("scientific_title", ""),
            "autori": None, "anno": int(anno.group(0)) if anno else None,
            "rivista": f"WHO ICTRP ({c.get('source_register', '')})".replace(" ()", ""),
            "pubtypes": f"Registry record; {c.get('study_type', '')}; source ictrp",
            "abstract": "\n".join(righe),
            "link": c.get("web_address", "") or f"https://trialsearch.who.int/Trial2.aspx?TrialID={tid}",
            # Un trial registrato in più registri: la registrazione in un altro
            # registro è un altro record, quindi l'ID secondario non fa duplicato
            # (alias vuoto); trial_noti() lo segnala soltanto.
            "alias": [], "secondari": [x for x in id_registro(sec) if x != ident],
            "trial_id": tid,
        }
    return len(trial), list(out.values())


# ------------------------------------------------------------------ risoluzione
def risolvi(con, recs: list[dict]) -> None:
    """Scrive in ogni record `esistente` (chiave nel DB o None) e `via`."""
    per_pmid = {r["pmid"] for r in con.execute("SELECT pmid FROM record")}
    per_doi = {r["doi"].lower(): r["pmid"] for r in
               con.execute("SELECT pmid, doi FROM record WHERE COALESCE(doi,'') != ''")}
    per_titolo: dict[str, str] = {}
    for r in con.execute("SELECT pmid, titolo FROM record"):
        per_titolo.setdefault(norma_titolo(r["titolo"]), r["pmid"])
    for r in recs:
        r["esistente"], r["via"] = None, None
        t = norma_titolo(r["titolo"])
        for via, chiave in (("pmid", r["pmid_vero"] if r["pmid_vero"] in per_pmid else None),
                            ("doi", per_doi.get(r["doi"].lower()) if r["doi"] else None),
                            ("id", r["id"] if r["id"] in per_pmid else None),
                            ("registro", next((a for a in r["alias"] if a in per_pmid), None)),
                            ("titolo", per_titolo.get(t) if len(t) >= 25 else None)):
            if chiave:
                r["esistente"], r["via"] = chiave, via
                break
        # Un record di registro nuovo prende l'identificativo del registro, come
        # quelli di fonti_meta.py: così un export successivo lo riconosce.
        if not r["esistente"] and r["alias"]:
            r["id"] = r["alias"][0]


def unici(recs: list[dict]) -> tuple[list[dict], list[str]]:
    """Toglie i doppioni interni all'export (stesso id, PMID o DOI)."""
    visti: dict[str, str] = {}
    tenuti, doppi = [], []
    for r in recs:
        chiavi = [f"id:{r['id']}"] + ([f"pmid:{r['pmid_vero']}"] if r["pmid_vero"] else []) \
                 + ([f"doi:{r['doi'].lower()}"] if r["doi"] else [])
        gia = next((visti[k] for k in chiavi if k in visti), None)
        if gia:
            doppi.append(f"{r['id']} = {gia}")
            continue
        for k in chiavi:
            visti[k] = r["id"]
        tenuti.append(r)
    return tenuti, doppi


def trial_noti(con, recs: list[dict]) -> list[str]:
    """Registrazioni ICTRP di trial già nella tabella `trial`, o il cui ID
    secondario è già un record del DB: solo un avviso, il record di registro si
    valuta comunque."""
    presenti = {r["pmid"] for r in con.execute("SELECT pmid FROM record")}
    out = [f"{r['id']}: ID secondario {s} già nel DB" for r in recs
           for s in r.get("secondari", []) if s in presenti and not r["esistente"]]
    righe = list(con.execute("SELECT trial_id, acronimo, altri_registri FROM trial"))
    for r in recs:
        tid = r.get("trial_id", "")
        nudo = (EUDRACT_RE.search(tid) or [None])[0] if tid.upper().startswith("EUCTR") else tid
        for t in righe:
            if nudo and nudo in f"{t['trial_id']} {t['altri_registri'] or ''}":
                out.append(f"{r['id']} = trial {t['trial_id']} ({t['acronimo']})")
    return out


# ------------------------------------------------------------------ scrittura
def da_pubmed(pmids: list[str]) -> dict[str, dict]:
    from pubmed_harvest import _base_params, _get, parse_article
    out = {}
    for i in range(0, len(pmids), 200):
        p = _base_params() | {"id": ",".join(pmids[i:i + 200]), "retmode": "xml"}
        for art in ET.fromstring(_get("efetch.fcgi", p).content).iterfind("PubmedArticle"):
            rec = parse_article(art)
            if rec:
                out[rec["pmid"]] = rec
    return out


def scrivi(con, fonte: str, recs: list[dict]) -> dict:
    from fonti_meta import inserisci
    from pubmed_harvest import upsert
    query = f"S-{fonte}"
    esito = {"nuovi_da_pubmed": [], "nuovi_da_export": [], "pmid_non_trovati_in_pubmed": []}
    articoli = da_pubmed([r["pmid_vero"] for r in recs if not r["esistente"] and r["pmid_vero"]])
    for r in recs:
        if r["esistente"]:
            corpus = con.execute("SELECT corpus FROM record WHERE pmid=?",
                                 (r["esistente"],)).fetchone()[0]
            if corpus == "wiki":
                con.execute("UPDATE record SET corpus='wiki+meta' WHERE pmid=?", (r["esistente"],))
            con.execute("INSERT OR IGNORE INTO record_query (pmid, query) VALUES (?,?)",
                        (r["esistente"], query))
        elif r["pmid_vero"] in articoli:
            upsert(con, articoli[r["pmid_vero"]], query, "meta")
            esito["nuovi_da_pubmed"].append(r["pmid_vero"])
        else:
            if r["pmid_vero"]:
                esito["pmid_non_trovati_in_pubmed"].append(f"{r['id']} (PMID {r['pmid_vero']})")
            inserisci(con, fonte, r)
            con.execute("INSERT OR IGNORE INTO record_query (pmid, query) VALUES (?,?)",
                        (r["id"], query))
            esito["nuovi_da_export"].append(r["id"])
    con.commit()
    return esito


def main() -> None:
    ap = argparse.ArgumentParser(description="Import degli export Embase, CENTRAL e ICTRP")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--embase", metavar="RIS")
    g.add_argument("--central", metavar="RIS")
    g.add_argument("--ictrp", metavar="XML", nargs="+",
                   help="un file, oppure due (lato FDI e lato FCM) da intersecare")
    ap.add_argument("--titoli", choices=["duplicati", "nuovi"],
                    help="come trattare i record che coincidono col DB solo per titolo")
    ap.add_argument("--eccetto", default="", help="ID dell'export trattati al contrario di --titoli")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.ictrp:
        if len(args.ictrp) > 2:
            ap.error("--ictrp accetta uno o due file")
        fonte, file = "ictrp", args.ictrp
        letti = [parse_ictrp(leggi(f)) for f in file]
        nel_file, lati = [n for n, _ in letti], [x for _, x in letti]
        recs = lati[0] if len(lati) == 1 else \
            [r for r in lati[0] if r["id"] in {x["id"] for x in lati[1]}]
    else:
        fonte = "embase" if args.embase else "central"
        file = [args.embase or args.central]
        grezzi = parse_ris(leggi(file[0]))
        nel_file = [len(grezzi)]
        recs = [da_ris(fonte, r) for r in grezzi]
    senza_titolo = [r["id"] for r in recs if not r["titolo"]]
    recs, doppi = unici(recs)

    init_db()
    con = connect()
    risolvi(con, recs)
    eccetto = {x.strip() for x in args.eccetto.split(",") if x.strip()}
    ignoti = eccetto - {r["id"] for r in recs if r["via"] == "titolo"}
    if ignoti:
        sys.exit(f"--eccetto: non sono sospetti per titolo: {', '.join(sorted(ignoti))}")
    sospetti = [r for r in recs if r["via"] == "titolo"]

    print(f"[{fonte}] record nei file: {' + '.join(map(str, nel_file))}"
          + (f"; in comune ai due file {len(recs) + len(doppi)}" if len(nel_file) == 2 else "")
          + f"; doppioni interni {len(doppi)}; distinti {len(recs)}")
    for via in ("pmid", "doi", "id", "registro"):
        n = sum(r["via"] == via for r in recs)
        if n:
            print(f"  già nel DB per {via}: {n}")
    print(f"  sospetti duplicati per solo titolo: {len(sospetti)}")
    for r in sospetti:
        e = con.execute("SELECT pmid, anno, rivista FROM record WHERE pmid=?",
                        (r["esistente"],)).fetchone()
        print(f"    {r['id']} ({r['anno']}, {r['rivista'][:40]}) ~ {e['pmid']} "
              f"({e['anno']}, {(e['rivista'] or '')[:40]})\n      {r['titolo'][:110]}")
    nuovi = [r for r in recs if not r["esistente"]]
    print(f"  nuovi: {len(nuovi)} (di cui {sum(bool(r['pmid_vero']) for r in nuovi)} con PMID)")
    if senza_titolo:
        print(f"  ATTENZIONE, record senza titolo: {', '.join(senza_titolo)}")
    noti = trial_noti(con, recs) if fonte == "ictrp" else []
    for t in noti:
        print(f"  registrazione di un trial già identificato: {t}")

    if args.dry_run:
        con.close()
        return
    if sospetti and not args.titoli:
        con.close()
        sys.exit("Import fermo: decidere i sospetti per titolo con --titoli duplicati|nuovi "
                 "[--eccetto ID,ID].")
    for r in sospetti:
        duplicato = (args.titoli == "duplicati") != (r["id"] in eccetto)
        r["decisione_titolo"] = "duplicato" if duplicato else "nuovo"
        if not duplicato:
            r["esistente"] = None
    esito = scrivi(con, fonte, recs)
    con.close()

    dest = LOG_DIR / f"export-meta-{date.today():%Y-%m-%d}.json"
    storico = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else []
    storico.append({
        "ts": now_iso(), "fonte": fonte, "file": [Path(f).name for f in file],
        "record_nei_file": nel_file, "doppioni_interni": doppi, "distinti": len(recs),
        "gia_presenti": {v: sorted(f"{r['id']} = {r['esistente']}" for r in recs
                                   if r["esistente"] and r["via"] == v)
                         for v in ("pmid", "doi", "id", "registro", "titolo")},
        "titoli_decisi_nuovi": sorted(r["id"] for r in sospetti
                                      if r["decisione_titolo"] == "nuovo"),
        "trial_gia_identificati": noti, "senza_titolo": senza_titolo, **esito,
    })
    dest.write_text(json.dumps(storico, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n_nuovi = len(esito["nuovi_da_pubmed"]) + len(esito["nuovi_da_export"])
    print(f"Importati {n_nuovi} nuovi ({len(esito['nuovi_da_pubmed'])} da PubMed, "
          f"{len(esito['nuovi_da_export'])} dall'export); {len(recs) - n_nuovi} già presenti. "
          f"Log: {dest.relative_to(LOG_DIR.parent.parent)}")
    for p in esito["pmid_non_trovati_in_pubmed"]:
        print(f"  PMID dell'export non trovato in PubMed, importato dall'export: {p}")


if __name__ == "__main__":
    sys.exit(main())
