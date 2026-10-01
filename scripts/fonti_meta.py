#!/usr/bin/env python3
"""Ricerca nelle fonti non-PubMed della meta-analisi (protocollo §7).

Fonti interrogate da qui, tutte pubbliche e senza autenticazione:

    python3 scripts/fonti_meta.py --ctgov        # ClinicalTrials.gov API v2
    python3 scripts/fonti_meta.py --euctr        # EU Clinical Trials Register
    python3 scripts/fonti_meta.py --ctis         # EU CTIS (Regolamento 536/2014)
    python3 scripts/fonti_meta.py --europepmc    # Europe PMC, esclusi i record MEDLINE
    python3 scripts/fonti_meta.py --tutte [--dry-run]

CENTRAL, Embase e WHO ICTRP si interrogano a mano (vietano o non offrono
l'accesso automatico); i loro export si importano con scripts/export_meta.py.

Ogni record entra nel corpus `meta` con un identificativo proprio nella colonna
`pmid`: NCT…, EUCTR-…, CTIS-…, EPMC-…. Un record che ha un PMID o un DOI già nel
DB non si duplica: riceve solo la fonte in record_query. Le stringhe, i
conteggi e i duplicati vanno nel log della ricerca.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from datetime import date

import requests

from common import DIR_ABSTRACT, LOG_DIR, USER_AGENT, connect, init_db, now_iso

FDI = ["ferric derisomaltose", "iron isomaltoside", "isomaltoside 1000", "Monofer",
       "Monoferric", "Diafer"]
FCM = ["ferric carboxymaltose", "carboxymaltose", "Ferinject", "Injectafer"]
H = {"User-Agent": USER_AGENT}


def _or(termini: list[str]) -> str:
    return "(" + " OR ".join(f'"{t}"' if " " in t else t for t in termini) + ")"


# ------------------------------------------------------------------ fonti
def ctgov() -> tuple[str, list[dict]]:
    term = f"{_or(FDI)} AND {_or(FCM)}"
    out, token = [], None
    while True:
        p = {"query.term": term, "pageSize": 100, "format": "json"}
        if token:
            p["pageToken"] = token
        d = requests.get("https://clinicaltrials.gov/api/v2/studies", params=p,
                         headers=H, timeout=60).json()
        for s in d["studies"]:
            ps = s["protocolSection"]
            idm, st = ps["identificationModule"], ps.get("statusModule", {})
            des = ps.get("designModule", {})
            arms = ps.get("armsInterventionsModule", {}).get("armGroups", [])
            refs = ps.get("referencesModule", {}).get("references", [])
            sec = [x.get("id", "") for x in idm.get("secondaryIdInfos", [])]
            righe = [
                f"Official title: {idm.get('officialTitle', '')}",
                f"Status: {st.get('overallStatus', '')}; start "
                f"{st.get('startDateStruct', {}).get('date', '')}; completion "
                f"{st.get('completionDateStruct', {}).get('date', '')}; "
                f"results posted: {s.get('hasResults', False)}",
                f"Study type: {des.get('studyType', '')}; allocation: "
                f"{des.get('designInfo', {}).get('allocation', '')}; phases: "
                f"{', '.join(des.get('phases', []))}; enrollment: "
                f"{des.get('enrollmentInfo', {}).get('count', '')}",
                "Conditions: " + "; ".join(ps.get("conditionsModule", {}).get("conditions", [])),
                "Eligibility: minimum age "
                f"{ps.get('eligibilityModule', {}).get('minimumAge', '')}",
                "Arms: " + " | ".join(
                    f"{a.get('label', '')} [{a.get('type', '')}]: "
                    f"{', '.join(a.get('interventionNames', []))}" for a in arms),
                "Secondary IDs: " + ", ".join(sec),
                "References (PMID): " + ", ".join(r["pmid"] for r in refs if r.get("pmid")),
                "Brief summary: " + ps.get("descriptionModule", {}).get("briefSummary", ""),
            ]
            anno = (st.get("startDateStruct", {}).get("date", "") or "")[:4]
            out.append({
                "id": idm["nctId"], "doi": "", "titolo": idm.get("briefTitle", ""),
                "anno": int(anno) if anno.isdigit() else None,
                "rivista": "ClinicalTrials.gov",
                "pubtypes": f"Registry record; {des.get('studyType', '')}; "
                            f"{des.get('designInfo', {}).get('allocation', '')}",
                "abstract": "\n".join(righe),
                "link": f"https://clinicaltrials.gov/study/{idm['nctId']}",
            })
        token = d.get("nextPageToken")
        if not token:
            break
    return f"query.term={term}", out


def euctr() -> tuple[str, list[dict]]:
    fdi = ["isomaltoside", "derisomaltose", "Monofer", "Monoferric", "Diafer"]
    fcm = ["carboxymaltose", "Ferinject", "Injectafer"]
    query = f"({' OR '.join(fdi)}) AND ({' OR '.join(fcm)})"
    url = "https://www.clinicaltrialsregister.eu/ctr-search/search"
    out, pagina, visti = [], 1, set()
    totale = None
    while True:
        t = requests.get(url, params={"query": query, "page": pagina}, headers=H,
                         timeout=60).text
        if totale is None:
            m = re.search(r"(\d+) result\(s\) found", t)
            totale = int(m.group(1)) if m else 0
        blocchi = t.split('<table class="result">')[1:]
        for b in blocchi:
            testo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", b))).strip()
            num = re.search(r"EudraCT Number:\s*(\d{4}-\d{6}-\d{2})", testo).group(1)
            titolo = re.search(r"Full Title:\s*(.*?)\s*Medical condition:", testo)
            inizio = re.search(r"Start Date \*?\s*:\s*(\d{4})", testo)
            if num in visti:
                continue
            visti.add(num)
            out.append({
                "id": f"EUCTR-{num}", "doi": "",
                "titolo": titolo.group(1) if titolo else "",
                "anno": int(inizio.group(1)) if inizio else None,
                "rivista": "EU Clinical Trials Register",
                "pubtypes": "Registry record",
                "abstract": testo,
                "link": f"https://www.clinicaltrialsregister.eu/ctr-search/search?query={num}",
            })
        if not blocchi or len(visti) >= totale:
            break
        pagina += 1
        time.sleep(1)
    return f"query={query}", out


def ctis() -> tuple[str, list[dict]]:
    """CTIS cerca un prodotto per volta: si cercano tutti i sinonimi di ciascun
    farmaco e si intersecano gli insiemi."""
    fdi = ["derisomaltose", "isomaltoside", "Monofer", "Monoferric", "Diafer"]
    fcm = ["carboxymaltose", "Ferinject", "Injectafer"]
    url = "https://euclinicaltrials.eu/ctis-public-api/search"

    def cerca(prodotto: str) -> dict[str, dict]:
        trovati, pagina = {}, 1
        while True:
            corpo = {"pagination": {"page": pagina, "size": 100},
                     "sort": {"property": "decisionDate", "direction": "DESC"},
                     "searchCriteria": {"productName": prodotto}}
            d = requests.post(url, json=corpo, headers=H, timeout=60).json()
            for x in d["data"]:
                trovati[x["ctNumber"]] = x
            if not d["pagination"].get("nextPage"):
                return trovati
            pagina += 1

    lato_fdi, lato_fcm = {}, {}
    for p in fdi:
        lato_fdi |= cerca(p)
    for p in fcm:
        lato_fcm |= cerca(p)
    comuni = sorted(set(lato_fdi) & set(lato_fcm))
    out = []
    for n in comuni:
        x = lato_fdi[n]
        out.append({
            "id": f"CTIS-{n}", "doi": "", "titolo": x.get("ctTitle", ""),
            "anno": None, "rivista": "EU CTIS", "pubtypes": "Registry record",
            "abstract": json.dumps(x, ensure_ascii=False),
            "link": f"https://euclinicaltrials.eu/search-for-clinical-trials/?lang=en&EUCT={n}",
        })
    desc = (f"productName ∈ {fdi} (unione: {len(lato_fdi)} trial) ∩ productName ∈ {fcm} "
            f"(unione: {len(lato_fcm)} trial)")
    return desc, out


def europepmc() -> tuple[str, list[dict]]:
    query = f"{_or(FDI)} AND {_or(FCM)} NOT SRC:MED"
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    out, cursor = [], "*"
    while True:
        d = requests.get(url, params={"query": query, "format": "json", "pageSize": 100,
                                      "resultType": "core", "cursorMark": cursor},
                         headers=H, timeout=60).json()
        for r in d["resultList"]["result"]:
            src, rid = r.get("source", ""), r.get("id", "")
            ident = f"EPMC-{rid}" if rid.startswith(src) else f"EPMC-{src}-{rid}"
            out.append({
                "id": ident, "pmid_vero": r.get("pmid") or "", "doi": r.get("doi") or "",
                "titolo": r.get("title", ""),
                "anno": int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None,
                "rivista": (r.get("journalInfo", {}).get("journal", {}).get("title")
                            or r.get("bookOrReportDetails", {}).get("publisher")
                            or src),
                "pubtypes": "; ".join(r.get("pubTypeList", {}).get("pubType", [])) + f"; source {src}",
                "abstract": re.sub(r"<[^>]+>", "", r.get("abstractText", "") or ""),
                "link": f"https://europepmc.org/article/{src}/{rid}",
            })
        nuovo = d.get("nextCursorMark")
        if not nuovo or nuovo == cursor or not d["resultList"]["result"]:
            break
        cursor = nuovo
    return f"query={query} (campi di default di Europe PMC, fulltext OA compreso)", out


def da_doi(dois: list[str], note: dict[str, str]) -> list[dict]:
    """Record identificati per DOI (Consensus, altri metodi): metadati e, se
    c'è, abstract da Crossref. `note` aggiunge testo quando Crossref non ha
    l'abstract, dichiarandone la provenienza."""
    out = []
    for d in dois:
        m = requests.get(f"https://api.crossref.org/works/{d}", headers=H,
                         timeout=60).json()["message"]
        ab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.get("abstract", "") or "")).strip()
        if not ab and d in note:
            ab = note[d]
        anno = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
        rivista = (m.get("container-title") or [""])[0]
        sede = " ".join(str(x) for x in (m.get("volume"), m.get("issue"), m.get("page")) if x)
        out.append({
            "id": "DOI-" + d.replace("/", "_"), "doi": d,
            "titolo": (m.get("title") or [""])[0], "anno": anno,
            "rivista": f"{rivista} {sede}".strip(),
            "pubtypes": "Conference abstract (journal supplement)"
                        if "upplement" in sede else m.get("type", ""),
            "abstract": ab or "Abstract non disponibile in Crossref.",
            "link": f"https://doi.org/{d}",
        })
    return out


def crossref() -> tuple[str, list[dict]]:
    """Crossref non ha sintassi booleana e ordina per pertinenza. Regola
    (protocollo §15, deviazione del 2026-09-29): per ogni coppia di sinonimi
    FDI × FCM si scorrono i risultati di query.bibliographic in ordine di
    pertinenza, fermandosi dopo FERMO risultati consecutivi senza
    corrispondenze o al TETTO; si tiene un record solo se titolo o abstract
    contengono almeno un termine FDI e almeno un termine FCM."""
    FERMO, TETTO = 200, 2000
    fdi = [t.lower() for t in FDI]
    fcm = [t.lower() for t in FCM]
    url = "https://api.crossref.org/works"
    campi = "DOI,title,abstract,type,container-title,volume,issue,page,issued,author"
    trovati: dict[str, dict] = {}
    dettaglio = []
    for a in fdi:
        for b in fcm:
            cursor, visti, vuoti, utili = "*", 0, 0, 0
            while visti < TETTO and vuoti < FERMO:
                m = requests.get(url, params={"query.bibliographic": f"{a} {b}",
                                              "rows": 200, "cursor": cursor,
                                              "select": campi},
                                 headers=H, timeout=90).json()["message"]
                if not m["items"]:
                    break
                for it in m["items"]:
                    visti += 1
                    testo = (" ".join(it.get("title") or []) + " "
                             + (it.get("abstract") or "")).lower()
                    if any(x in testo for x in fdi) and any(x in testo for x in fcm):
                        trovati[it["DOI"].lower()] = it
                        utili += 1
                        vuoti = 0
                    else:
                        vuoti += 1
                    if vuoti >= FERMO or visti >= TETTO:
                        break
                cursor = m.get("next-cursor")
                time.sleep(1)
            dettaglio.append(f"'{a} {b}': {visti} scorsi, {utili} utili")
    out = []
    for d, m in sorted(trovati.items()):
        ab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.get("abstract", "") or "")).strip()
        anno = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
        rivista = (m.get("container-title") or [""])[0]
        sede = " ".join(str(x) for x in (m.get("volume"), m.get("issue"), m.get("page")) if x)
        au = m.get("author") or []
        primo = au[0].get("family", "") if au else ""
        out.append({
            "id": "DOI-" + d.replace("/", "_"), "doi": d,
            "titolo": (m.get("title") or [""])[0], "anno": anno,
            "rivista": f"{rivista} {sede}".strip(),
            "pubtypes": f"Crossref type {m.get('type', '')}"
                        + ("; journal supplement" if "uppl" in sede else ""),
            "abstract": (f"Primo autore: {primo}. " if primo else "")
                        + (ab or "Abstract non disponibile in Crossref."),
            "link": f"https://doi.org/{d}",
        })
    desc = (f"query.bibliographic per 24 coppie FDI×FCM, stop dopo {FERMO} consecutivi "
            f"senza corrispondenze o a {TETTO}; filtro locale titolo+abstract "
            f"(≥1 termine FDI e ≥1 FCM). " + "; ".join(dettaglio))
    return desc, out


FONTI = {"ctgov": ctgov, "euctr": euctr, "ctis": ctis, "europepmc": europepmc,
         "crossref": crossref}


# ------------------------------------------------------------------ scrittura
def inserisci(con, fonte: str, r: dict) -> None:
    """Nuovo record del corpus meta con identificativo proprio, e il suo file
    in 90-Sorgenti/abstract/. Usata anche da export_meta.py."""
    con.execute(
        """INSERT INTO record (pmid, doi, titolo, autori, anno, rivista, pubtypes, abstract,
                               primo_harvest, ultimo_aggiornamento, corpus)
           VALUES (?,?,?,?,?,?,?,?,?,?, 'meta')""",
        (r["id"], r.get("doi", ""), r["titolo"], r.get("autori"), r["anno"], r["rivista"],
         r["pubtypes"], f"{r['abstract']}\n\nFonte: {r['link']}",
         now_iso(), now_iso()))
    (DIR_ABSTRACT / f"{r['id']}.md").write_text(
        f"---\nid: \"{r['id']}\"\nfonte: {fonte}\nlink: {r['link']}\n---\n\n"
        f"# {r['titolo']}\n\n{r['abstract']}\n", encoding="utf-8")


def importa(fonte: str, recs: list[dict], dry: bool) -> dict:
    con = connect()
    esito = {"identificati": len(recs), "nuovi": 0, "gia_presenti": 0, "duplicati": []}
    for r in recs:
        # Duplicato se il record ha un PMID già nel DB, o un DOI già nel DB.
        doppio = None
        if r.get("pmid_vero"):
            doppio = con.execute("SELECT pmid FROM record WHERE pmid=?",
                                 (r["pmid_vero"],)).fetchone()
        if not doppio and r.get("doi"):
            doppio = con.execute("SELECT pmid FROM record WHERE lower(doi)=lower(?)",
                                 (r["doi"],)).fetchone()
        if not doppio:
            doppio = con.execute("SELECT pmid FROM record WHERE pmid=?", (r["id"],)).fetchone()
        chiave = doppio["pmid"] if doppio else r["id"]
        if doppio and doppio["pmid"] != r["id"]:
            esito["duplicati"].append(f"{r['id']} = {doppio['pmid']}")
        if dry:
            esito["gia_presenti" if doppio else "nuovi"] += 1
            continue
        if doppio:
            corpus = con.execute("SELECT corpus FROM record WHERE pmid=?", (chiave,)).fetchone()[0]
            if corpus == "wiki":
                con.execute("UPDATE record SET corpus='wiki+meta' WHERE pmid=?", (chiave,))
            esito["gia_presenti"] += 1
        else:
            inserisci(con, fonte, r)
            esito["nuovi"] += 1
        con.execute("INSERT OR IGNORE INTO record_query (pmid, query) VALUES (?,?)",
                    (chiave, f"S-{fonte}"))
    con.commit()
    con.close()
    return esito


def main() -> None:
    ap = argparse.ArgumentParser(description="Fonti non-PubMed della meta-analisi")
    for f in FONTI:
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--tutte", action="store_true")
    ap.add_argument("--doi-json", metavar="FILE",
                    help='importa per DOI: {"fonte": "...", "stringa": "...", '
                         '"doi": [...], "note": {doi: testo}}')
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    scelte = [f for f in FONTI if args.tutte or getattr(args, f)]
    if not scelte and not args.doi_json:
        ap.error("indica almeno una fonte, --tutte oppure --doi-json")
    init_db()
    righe = []
    if args.doi_json:
        spec = json.loads(open(args.doi_json, encoding="utf-8").read())
        recs = da_doi(spec["doi"], spec.get("note", {}))
        e = importa(spec["fonte"], recs, args.dry_run)
        print(f"[{spec['fonte']}] identificati {e['identificati']}, nuovi {e['nuovi']}, "
              f"già presenti {e['gia_presenti']}")
        for d in e["duplicati"]:
            print(f"   duplicato: {d}")
        righe.append((spec["fonte"], spec["stringa"], e))
    for f in scelte:
        stringa, recs = FONTI[f]()
        e = importa(f, recs, args.dry_run)
        print(f"[{f}] identificati {e['identificati']}, nuovi {e['nuovi']}, "
              f"già presenti {e['gia_presenti']}")
        for d in e["duplicati"]:
            print(f"   duplicato: {d}")
        righe.append((f, stringa, e))
    if args.dry_run:
        return
    dest = LOG_DIR / f"fonti-meta-{date.today():%Y-%m-%d}.json"
    storico = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else []
    storico += [{"ts": now_iso(), "fonte": f, "stringa": s, **e} for f, s, e in righe]
    dest.write_text(json.dumps(storico, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Log: {dest.relative_to(LOG_DIR.parent.parent)}")


if __name__ == "__main__":
    sys.exit(main())
