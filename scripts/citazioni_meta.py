#!/usr/bin/env python3
"""Ricerca per citazione della meta-analisi (protocollo §7), su Europe PMC.

    python3 scripts/citazioni_meta.py --dry-run
    python3 scripts/citazioni_meta.py

Semi:
- all'indietro: riferimenti delle pubblicazioni incluse in fase 2 (con PMID),
  delle revisioni sistematiche e meta-analisi del corpus meta escluse con E3,
  e delle revisioni in 99-Meta/fonti-di-riferimenti.md;
- in avanti: articoli che citano le pubblicazioni incluse in fase 2.

Un candidato non ancora nel DB entra nel corpus meta (fonte S-citazioni) se
titolo o abstract nominano FDI e FCM, oppure nominano uno dei due o il ferro EV
e il record è randomizzato (vedi largo()). I riferimenti senza identificativo il cui titolo nomina i due
farmaci si elencano nel log, per il recupero per DOI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date

import requests

from common import LOG_DIR, META, USER_AGENT, connect, init_db
from pubmed_harvest import parse_article, upsert, _base_params, _get

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
H = {"User-Agent": USER_AGENT}
FDI = ["ferric derisomaltose", "iron isomaltoside", "isomaltoside", "derisomaltose",
       "monofer", "monoferric", "diafer"]
FCM = ["ferric carboxymaltose", "carboxymaltose", "ferinject", "injectafer"]


def entrambi(t: str) -> bool:
    t = (t or "").lower()
    return any(x in t for x in FDI) and any(x in t for x in FCM)


IV = ["intravenous iron", "iv iron", "i.v. iron", "parenteral iron", "intravenous ferric"]


def largo(t: str, pubtypes: str = "") -> bool:
    """Filtro allargato (2026-09-29): il protocollo di RAPIDIRON (34556166) parla
    di «two different intravenous formulations» senza nominare FDI né FCM, e il
    filtro a due termini lo perdeva. Un record che nomina un farmaco o il ferro EV
    ed è randomizzato passa allo screening."""
    t = (t or "").lower()
    randomizzato = "randomized controlled trial" in (pubtypes or "").lower() or "randomi" in t
    return entrambi(t) or (randomizzato and any(x in t for x in FDI + FCM + IV))


def uno(t: str) -> bool:
    t = (t or "").lower()
    return any(x in t for x in FDI + FCM)


def lista(pmid: str, tipo: str) -> list[dict]:
    chiave = "referenceList" if tipo == "references" else "citationList"
    voce = "reference" if tipo == "references" else "citation"
    out, pagina = [], 1
    while True:
        d = requests.get(f"{EPMC}/MED/{pmid}/{tipo}", params={"format": "json",
                         "pageSize": 1000, "page": pagina}, headers=H, timeout=90).json()
        L = (d.get(chiave) or {}).get(voce, [])
        out += L
        if len(out) >= int(d.get("hitCount", 0)) or not L:
            return out
        pagina += 1


def semi() -> tuple[list[str], list[str]]:
    con = connect()
    inclusi = [r[0] for r in con.execute(
        "SELECT pmid FROM record WHERE stato_eleggibilita_meta='incluso' AND pmid GLOB '[0-9]*'")]
    rev = [r[0] for r in con.execute(
        "SELECT pmid FROM record WHERE corpus != 'wiki' AND motivo_screening_meta LIKE 'E3%' "
        "AND pmid GLOB '[0-9]*' AND (pubtypes LIKE '%Systematic%' OR pubtypes LIKE '%Meta-Analysis%' "
        "OR lower(titolo) LIKE '%meta-analy%' OR lower(titolo) LIKE '%systematic%')")]
    con.close()
    fonti = re.findall(r"^\| (\d{7,8}) \|", (META / "fonti-di-riferimenti.md").read_text(), re.M)
    indietro = sorted(set(inclusi) | set(rev) | set(fonti))
    return indietro, sorted(inclusi)


def dettagli_epmc(ids: list[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    """Titolo e abstract dei candidati non-MEDLINE da Europe PMC."""
    out = {}
    for src, rid in ids:
        d = requests.get(f"{EPMC}/search", params={"query": f"EXT_ID:{rid} AND SRC:{src}",
                         "format": "json", "resultType": "core"}, headers=H, timeout=60).json()
        r = (d.get("resultList", {}).get("result") or [{}])[0]
        out[(src, rid)] = r
        time.sleep(0.2)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Ricerca per citazione (meta-analisi)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    init_db()
    indietro, avanti = semi()
    print(f"semi all'indietro {len(indietro)}, in avanti {len(avanti)}")

    trovati: dict[tuple[str, str], dict] = {}
    senza_id: list[dict] = []
    for p in indietro:
        for r in lista(p, "references"):
            if r.get("id") and r.get("source"):
                trovati.setdefault((r["source"], r["id"]), {"via": set(), **r})["via"].add(f"rif-di-{p}")
            elif uno(r.get("title", "")):
                senza_id.append({"da": p, **{k: r.get(k) for k in ("title", "doi", "journalAbbreviation", "pubYear")}})
        time.sleep(0.2)
    for p in avanti:
        for r in lista(p, "citations"):
            if r.get("id") and r.get("source"):
                trovati.setdefault((r["source"], r["id"]), {"via": set(), **r})["via"].add(f"cita-{p}")
        time.sleep(0.2)
    print(f"identificativi distinti raccolti: {len(trovati)}; riferimenti senza id con un "
          f"termine FDI/FCM nel titolo: {len(senza_id)}")

    con = connect()
    noti = {r[0] for r in con.execute("SELECT pmid FROM record")}
    doi_noti = {(r[0] or "").lower() for r in con.execute("SELECT doi FROM record")}
    nuovi = {k: v for k, v in trovati.items()
             if not (k[0] == "MED" and k[1] in noti)
             and not ((v.get("doi") or "").lower() in doi_noti and v.get("doi"))}
    print(f"non già nel DB: {len(nuovi)}")

    # Titolo e abstract: PubMed per i MED, Europe PMC per gli altri.
    med = [k[1] for k in nuovi if k[0] == "MED"]
    articoli = {}
    for i in range(0, len(med), 200):
        p = _base_params() | {"id": ",".join(med[i:i + 200]), "retmode": "xml"}
        root = ET.fromstring(_get("efetch.fcgi", p).content)
        for art in root.iterfind("PubmedArticle"):
            rec = parse_article(art)
            if rec:
                articoli[rec["pmid"]] = rec
    altri = dettagli_epmc([k for k in nuovi if k[0] != "MED"])

    tenuti = []
    for k, v in nuovi.items():
        if k[0] == "MED":
            rec = articoli.get(k[1])
            testo = f"{rec['titolo']} {rec['abstract']}" if rec else v.get("title", "")
            pt = rec["pubtypes"] if rec else ""
        else:
            r = altri.get(k, {})
            testo = f"{r.get('title', '')} {r.get('abstractText', '')}"
            pt = "; ".join(r.get("pubTypeList", {}).get("pubType", []))
        if largo(testo, pt):
            tenuti.append((k, v, articoli.get(k[1]) if k[0] == "MED" else altri.get(k)))
    print(f"tenuti dal filtro (entrambi i farmaci, oppure farmaco/ferro EV + randomizzato): {len(tenuti)}")
    for k, v, r in tenuti:
        tit = (r or {}).get("titolo") or (r or {}).get("title") or v.get("title", "")
        print(f"  {k[0]}:{k[1]}  {(tit or '')[:95]}  ← {', '.join(sorted(v['via']))[:60]}")
    for s in senza_id:
        if entrambi(s.get("title", "")):
            print(f"  [senza id] {s.get('title', '')[:100]} ({s.get('journalAbbreviation')}, "
                  f"{s.get('pubYear')}) ← rif-di-{s['da']}")
    if args.dry_run:
        return

    importati = 0
    for k, v, r in tenuti:
        if k[0] == "MED" and r:
            if upsert(con, r, "S-citazioni", "meta") == "nuovo":
                importati += 1
        else:
            print(f"  da importare a parte (non MEDLINE): {k}")
    con.commit()
    con.close()
    dest = LOG_DIR / f"citazioni-meta-{date.today():%Y-%m-%d}.json"
    dest.write_text(json.dumps({
        "semi_indietro": indietro, "semi_avanti": avanti,
        "identificativi_raccolti": len(trovati), "non_nel_db": len(nuovi),
        "tenuti": [f"{k[0]}:{k[1]}" for k, _, _ in tenuti], "importati": importati,
        "senza_id_con_entrambi": [s for s in senza_id if entrambi(s.get("title", ""))],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"importati {importati}; log {dest.relative_to(LOG_DIR.parent.parent)}")


if __name__ == "__main__":
    sys.exit(main())
