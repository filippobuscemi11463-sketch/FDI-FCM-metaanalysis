#!/usr/bin/env python3
"""Recupera le sorgenti per la fase 2 della meta-analisi dei record non-PubMed
inclusi in fase 1 (criteri-screening-meta.md). Solo canali pubblici e aperti.

    python3 scripts/sorgenti_meta.py            # tutti i record da recuperare
    python3 scripts/sorgenti_meta.py --id NCT03238911 EPMC-PMC9548091

Per tipo di identificativo:
- NCT…     scheda completa da ClinicalTrials.gov API v2, risultati compresi;
- EUCTR-…  pagine pubbliche del protocollo e dei risultati di EU CTR;
- EPMC-PMC… testo integrale da Europe PMC; per i volumi di abstract si
            estraggono le sezioni che nominano sia FDI sia FCM (regola dei
            volumi, criteri v1.2) in un file a parte;
- EPMC-PPR… testo del preprint da Europe PMC, se esiste;
- DOI-…    Unpaywall (best_oa_location), altrimenti resta da recuperare.

Il sorgente va in 90-Sorgenti/fulltext/<id>.md; il record riceve fulltext='si'
e fonte_fulltext = registro | europepmc-oa | unpaywall. I mancanti restano
fulltext='no' con il motivo, per il recupero manuale.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time

import requests
from pathlib import Path

from common import DIR_FULLTEXT, IN_META, UNPAYWALL_EMAIL, USER_AGENT, connect, now_iso

H = {"User-Agent": USER_AGENT}
FDI = ["ferric derisomaltose", "iron isomaltoside", "isomaltoside", "derisomaltose",
       "monofer", "monoferric", "diafer"]
FCM = ["ferric carboxymaltose", "carboxymaltose", "ferinject", "injectafer"]


def entrambi(t: str) -> bool:
    t = t.lower()
    return any(x in t for x in FDI) and any(x in t for x in FCM)


def testo(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


# ------------------------------------------------------------------ canali
def nct(ident: str) -> tuple[str, str] | None:
    r = requests.get(f"https://clinicaltrials.gov/api/v2/studies/{ident}", headers=H, timeout=60)
    if r.status_code != 200:
        return None
    d = r.json()
    corpo = [f"# {ident}", "", "Fonte: ClinicalTrials.gov API v2, scheda completa.", ""]
    for sezione in ("protocolSection", "resultsSection", "derivedSection"):
        if sezione in d:
            corpo += [f"## {sezione}", "", "```json",
                      json.dumps(d[sezione], ensure_ascii=False, indent=1), "```", ""]
    corpo.append(f"hasResults: {d.get('hasResults', False)}")
    return "\n".join(corpo), "registro"


def euctr(ident: str) -> tuple[str, str] | None:
    num = ident.removeprefix("EUCTR-")
    base = "https://www.clinicaltrialsregister.eu/ctr-search"
    s = requests.get(f"{base}/search", params={"query": num}, headers=H, timeout=60).text
    paesi = sorted(set(re.findall(rf"/ctr-search/trial/{num}/([A-Z]{{2,3}})", s)))
    corpo = [f"# {ident}", "", "Fonte: EU Clinical Trials Register, pagine pubbliche.", ""]
    for p in (paesi[:1] or []):
        t = requests.get(f"{base}/trial/{num}/{p}", headers=H, timeout=60).text
        corpo += [f"## Protocollo ({p})", "", testo(t)[:60000], ""]
        time.sleep(1)
    if "results" in s:
        t = requests.get(f"{base}/trial/{num}/results", headers=H, timeout=60)
        if t.status_code == 200:
            corpo += ["## Risultati", "", testo(t.text)[:60000], ""]
    return ("\n".join(corpo), "registro") if len(corpo) > 4 else None


def epmc_fulltext(pmcid: str) -> str | None:
    r = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
                     headers=H, timeout=90)
    return r.content.decode("utf-8", "replace") if r.status_code == 200 and r.content else None


def finestre(t: str, raggio: int = 1500, vicinanza: int = 3000) -> list[str]:
    """Brani in cui un termine FDI e un termine FCM compaiono a meno di
    `vicinanza` caratteri; ±`raggio` di contesto, sovrapposizioni fuse."""
    basso = t.lower()
    pos = lambda termini: sorted(m.start() for x in termini for m in re.finditer(re.escape(x), basso))
    pf, pc = pos(FDI), pos(FCM)
    intervalli = []
    for a in pf:
        if any(abs(a - b) <= vicinanza for b in pc):
            intervalli.append([max(0, a - raggio), min(len(t), a + raggio)])
    fusi: list[list[int]] = []
    for i in sorted(intervalli):
        if fusi and i[0] <= fusi[-1][1]:
            fusi[-1][1] = max(fusi[-1][1], i[1])
        else:
            fusi.append(i)
    return [t[i:j] for i, j in fusi]


def epmc(ident: str) -> tuple[str, str] | None:
    """Regola dei volumi (criteri v1.2): si individuano i brani con FDI e FCM
    vicini. Oltre GRANDE caratteri si salvano solo i brani, con il rimando al
    testo integrale su Europe PMC: i volumi di abstract pesano milioni di
    caratteri e il resto non serve alla meta-analisi."""
    GRANDE = 200_000
    rid = ident.removeprefix("EPMC-")
    xml = epmc_fulltext(rid)
    if not xml:
        return None
    t = testo(xml)
    brani = finestre(t)
    corpo = [f"# {ident}", "", "Fonte: Europe PMC fullTextXML.", "",
             f"Brani con un termine FDI e uno FCM a meno di 3000 caratteri: {len(brani)}.", ""]
    for k, b in enumerate(brani, 1):
        corpo += [f"## Brano {k}", "", b, ""]
    if len(t) <= GRANDE:
        corpo += ["## Testo integrale", "", t]
    else:
        corpo += ["## Testo integrale", "",
                  f"Non salvato ({len(t):,} caratteri). Testo completo: "
                  f"https://europepmc.org/article/PMC/{rid}"]
    return "\n".join(corpo), "europepmc-oa"


def doi_oa(ident: str, doi: str) -> tuple[str, str] | None:
    if not UNPAYWALL_EMAIL or not doi:
        return None
    r = requests.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": UNPAYWALL_EMAIL},
                     headers=H, timeout=60)
    if r.status_code != 200:
        return None
    loc = (r.json() or {}).get("best_oa_location") or {}
    url = loc.get("url_for_landing_page") or loc.get("url")
    if not url:
        return None
    p = requests.get(url, headers=H, timeout=60)
    if p.status_code != 200 or "html" not in p.headers.get("content-type", ""):
        return None
    t = testo(re.sub(r"(?is)<(script|style).*?</\1>", " ", p.text))
    if not entrambi(t):
        return None
    return f"# {ident}\n\nFonte: Unpaywall → {url}\n\n{t}", "unpaywall"


# ------------------------------------------------------------- supplementi
def supplementi(ident: str, pmcid: str) -> str:
    """Materiali supplementari di un articolo PMC (codebook 1.1, §6.1): zip da
    Europe PMC, conversione in testo di PDF, Word ed Excel, un solo file
    90-Sorgenti/fulltext/<id>-suppl.md. I PDF originali vanno in
    90-Sorgenti/pdf/<id>-suppl-<n>.pdf (non versionati)."""
    import io
    import subprocess
    import tempfile
    import zipfile
    from common import DIR_PDF
    dest = DIR_FULLTEXT / f"{ident}-suppl.md"
    if dest.exists():
        return "già presente"
    r = requests.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles",
                     headers=H, timeout=120)
    if r.status_code != 200 or not r.content.startswith(b"PK"):
        return f"nessun supplemento (HTTP {r.status_code})"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    parti, n_pdf = [], 0
    for nome in sorted(z.namelist()):
        low = nome.lower()
        dati = z.read(nome)
        testo = ""
        if low.endswith(".pdf"):
            n_pdf += 1
            pdf = DIR_PDF / f"{ident}-suppl-{n_pdf}.pdf"
            pdf.write_bytes(dati)
            testo = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                                   capture_output=True, text=True).stdout
        elif low.endswith((".docx", ".doc", ".rtf", ".odt")):
            with tempfile.TemporaryDirectory() as td:
                f = Path(td) / Path(nome).name
                f.write_bytes(dati)
                testo = subprocess.run(["pandoc", str(f), "-t", "plain", "--wrap=none"],
                                       capture_output=True, text=True).stdout
        elif low.endswith((".xlsx", ".xls")):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(dati), data_only=True, read_only=True)
            for ws in wb.worksheets:
                testo += f"\n### Foglio {ws.title}\n\n"
                for row in ws.iter_rows(values_only=True):
                    if any(c is not None for c in row):
                        testo += " | ".join("" if c is None else str(c) for c in row) + "\n"
        elif low.endswith((".txt", ".csv")):
            testo = dati.decode("utf-8", "replace")
        if testo.strip():
            parti.append(f"## {nome}\n\n{testo}")
    if not parti:
        return "supplemento senza testo utilizzabile (solo immagini)"
    dest.write_text(f"# {ident} — materiali supplementari\n\nFonte: Europe PMC "
                    f"supplementaryFiles, {pmcid}.\n\n" + "\n\n".join(parti), encoding="utf-8")
    return f"✓ {len(parti)} file, {sum(len(p) for p in parti):,} caratteri"


# ------------------------------------------------------------------ main
def recupera(rec) -> str:
    ident, doi = rec["pmid"], rec["doi"]
    if ident.startswith("NCT"):
        res = nct(ident)
    elif ident.startswith("EUCTR-"):
        res = euctr(ident)
    elif ident.startswith("EPMC-"):
        res = epmc(ident)
    elif ident.startswith("DOI-"):
        res = doi_oa(ident, doi)
    else:
        return "saltato (PubMed: usare fulltext_fetch.py)"
    con = connect()
    if res:
        md, fonte = res
        (DIR_FULLTEXT / f"{ident}.md").write_text(md, encoding="utf-8")
        con.execute("UPDATE record SET fulltext='si', fonte_fulltext=?, fulltext_path=?, "
                    "fulltext_motivo=NULL, ultimo_aggiornamento=? WHERE pmid=?",
                    (fonte, f"90-Sorgenti/fulltext/{ident}.md", now_iso(), ident))
        esito = f"✓ {fonte} ({len(md):,} caratteri)"
        m = re.search(r"Brani con un termine FDI e uno FCM[^:]*: (\d+)", md)
        if m:
            esito += f"; {m.group(1)} brani con FDI e FCM"
    else:
        con.execute("UPDATE record SET fulltext_motivo='OA-non-trovato', "
                    "tentativi_fulltext=tentativi_fulltext+1, ultimo_aggiornamento=? "
                    "WHERE pmid=?", (now_iso(), ident))
        esito = "✗ nessun canale aperto → recupero manuale"
    con.commit()
    con.close()
    return esito


def main() -> None:
    ap = argparse.ArgumentParser(description="Sorgenti per la fase 2 della meta-analisi")
    ap.add_argument("--id", nargs="+", help="identificativi specifici")
    ap.add_argument("--supplementi", action="store_true",
                    help="materiali supplementari delle pubblicazioni incluse in fase 2")
    args = ap.parse_args()
    if args.supplementi:
        con = connect()
        rows = con.execute(
            "SELECT pmid, pmcid FROM record WHERE stato_eleggibilita_meta='incluso'").fetchall()
        con.close()
        for r in rows:
            pmcid = r["pmcid"] or (r["pmid"].removeprefix("EPMC-") if r["pmid"].startswith("EPMC-PMC")
                                   and "-" not in r["pmid"].removeprefix("EPMC-") else "")
            if pmcid:
                print(f"[{r['pmid']}] {supplementi(r['pmid'], pmcid)}", flush=True)
                time.sleep(1)
        return
    con = connect()
    if args.id:
        rows = con.execute("SELECT pmid, doi FROM record WHERE pmid IN (%s)"
                           % ",".join("?" * len(args.id)), args.id).fetchall()
    else:
        rows = con.execute(f"SELECT pmid, doi FROM record WHERE {IN_META} "
                           "AND stato_screening_meta='incluso' AND fulltext!='si' "
                           "AND pmid NOT GLOB '[0-9]*' ORDER BY pmid").fetchall()
    con.close()
    for r in rows:
        print(f"[{r['pmid']}] {recupera(r)}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
