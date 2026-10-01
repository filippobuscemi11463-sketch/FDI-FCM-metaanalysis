#!/usr/bin/env python3
"""GRADE della meta-analisi (99-Meta/grade-meta.md; protocollo §12).

    python3 scripts/grade_meta.py --valida FILE.csv
    python3 scripts/grade_meta.py --confronta A.csv B.csv [--out diff.md]
    python3 scripts/grade_meta.py --unisci CONSENSO.csv
    python3 scripts/grade_meta.py --sof

--valida controlla che ogni riga corrisponda a un risultato principale di
50-Metanalisi/output/risultati.csv (stessi k e partecipanti) e ricalcola la
certezza dalla somma dei punteggi. --sof genera 50-Metanalisi/sof.md e
50-Metanalisi/grade.md da grade.csv e dagli output dello script R: nessun
numero viene scritto a mano.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from common import VAULT_ROOT

MA = Path(VAULT_ROOT) / "50-Metanalisi"
OUT = MA / "output"
GRADE = MA / "grade.csv"
DOMINI = ["rischio_bias", "incoerenza", "indirettezza", "imprecisione", "pubblicazione"]
COL = (["esito", "finestra", "k", "partecipanti"] + DOMINI
       + [f"motivo_{d}" for d in DOMINI] + ["certezza", "frase", "valutatore"])
CERTEZZE = ["alta", "moderata", "bassa", "molto-bassa"]
NOMI = {"rischio_bias": "Rischio di bias", "incoerenza": "Incoerenza",
        "indirettezza": "Indirettezza", "imprecisione": "Imprecisione",
        "pubblicazione": "Bias di pubblicazione"}
ESITI = {"P1": "Ipofosfatemia (< 0,65 mmol/L)", "S1": "Ipofosfatemia grave (≤ 0,32 mmol/L)",
         "S2": "Ipofosfatemia a soglia larga (< 0,80 mmol/L)", "S3": "Ipofosfatemia persistente",
         "S4": "Variazione del fosfato (mmol/L)", "S5": "Osteomalacia e fratture",
         "S6": "Ipersensibilità grave", "S7": "Ipersensibilità, qualsiasi",
         "S8a": "Eventi cardiovascolari aggiudicati", "S8b": "SAE cardiaci e vascolari"}


def leggi(path, colonne=None) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        if colonne and (r.fieldnames or []) != colonne:
            sys.exit(f"{path}: intestazione diversa da quella attesa:\n{','.join(colonne)}")
        return list(r)


def principali() -> dict[tuple, list[dict]]:
    out: dict[tuple, list[dict]] = {}
    for r in leggi(OUT / "risultati.csv"):
        if r["analisi"] == "principale":
            out.setdefault((r["esito"], r["finestra"]), []).append(r)
    return out


def certezza(r: dict) -> str:
    tot = sum(int(r[d]) for d in DOMINI)
    return CERTEZZE[min(-tot, 3)]


def valida(path) -> list[str]:
    rows = leggi(path, COL)
    pr = principali()
    err, visti = [], set()
    for i, r in enumerate(rows, 2):
        key = (r["esito"], r["finestra"])
        dove = f"riga {i} ({r['esito']} {r['finestra']})"
        if key in visti:
            err.append(f"{dove}: duplicata")
        visti.add(key)
        if key not in pr:
            err.append(f"{dove}: nessun risultato principale in risultati.csv")
            continue
        p = pr[key][0]
        if r["k"] != p["k"] or r["partecipanti"] != p["partecipanti"]:
            err.append(f"{dove}: k/partecipanti {r['k']}/{r['partecipanti']} diversi dallo script "
                       f"({p['k']}/{p['partecipanti']})")
        ok = True
        for d in DOMINI:
            if r[d] not in {"0", "-1", "-2"}:
                err.append(f"{dove}: {d}={r[d]!r} fuori dominio"); ok = False
            if not r[f"motivo_{d}"].strip():
                err.append(f"{dove}: motivo_{d} vuoto")
        if ok and r["certezza"] != certezza(r):
            err.append(f"{dove}: certezza {r['certezza']} ma i punteggi danno {certezza(r)}")
        if not r["frase"].strip():
            err.append(f"{dove}: frase vuota")
        if r["valutatore"] not in {"A", "B", "consenso"}:
            err.append(f"{dove}: valutatore fuori dominio")
    mancanti = set(pr) - visti
    if mancanti:
        err.append("risultati principali senza riga GRADE: " + ", ".join(f"{e} {f}" for e, f in sorted(mancanti)))
    return err


def confronta(pa, pb, out) -> None:
    a = {(r["esito"], r["finestra"]): r for r in leggi(pa, COL)}
    b = {(r["esito"], r["finestra"]): r for r in leggi(pb, COL)}
    righe = ["# Confronto GRADE, A e B", "", "| Esito | Finestra | Campo | A | B |", "|---|---|---|---|---|"]
    n = 0
    for k in sorted(set(a) | set(b)):
        if k not in a or k not in b:
            righe.append(f"| {k[0]} | {k[1]} | riga | {'sì' if k in a else '—'} | {'sì' if k in b else '—'} |"); n += 1
            continue
        for c in DOMINI + ["certezza"]:
            if a[k][c] != b[k][c]:
                righe.append(f"| {k[0]} | {k[1]} | {c} | {a[k][c]} | {b[k][c]} |"); n += 1
    righe.insert(2, f"Differenze: {n}.\n")
    testo = "\n".join(righe) + "\n"
    if out:
        Path(out).write_text(testo, encoding="utf-8")
    print(testo)


def unisci(path) -> None:
    err = valida(path)
    if err:
        sys.exit("Validazione fallita:\n  " + "\n  ".join(err))
    rows = leggi(path, COL)
    if any(r["valutatore"] != "consenso" for r in rows):
        sys.exit("Si uniscono solo righe di consenso")
    with open(GRADE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COL)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} righe scritte in {GRADE.relative_to(VAULT_ROOT)}")


def fmt(x: str, dec: int = 2) -> str:
    if x in ("", None):
        return ""
    v = float(x)
    s = f"{v:.{dec}f}" if abs(v) >= 0.01 or v == 0 else f"{v:.3g}"
    return s.replace(".", ",")


def testi_sof() -> tuple[str, str]:
    """Testi di sof.md e grade.md, generati da grade.csv e dagli output dello script R."""
    g = leggi(GRADE, COL)
    err = valida(GRADE)
    if err:
        sys.exit("grade.csv non valido:\n  " + "\n  ".join(err))
    pr = principali()
    singoli = leggi(OUT / "trial-singoli.csv")
    run = (OUT / "run.txt").read_text(encoding="utf-8").splitlines()
    commit = next((l.strip() for l in run if l.startswith("Commit HEAD")), "")
    sha = next((l.strip() for l in run if l.startswith("SHA-256")), "")

    s = ["---", "tipo: meta-analisi", "descrizione: Summary of Findings, generata da scripts/grade_meta.py --sof",
         "---", "", "# Summary of Findings — FDI rispetto a FCM", "",
         f"Fonte dei numeri: `50-Metanalisi/output/` ({commit}; {sha}). Giudizi: `50-Metanalisi/grade.csv`.",
         "Effetti relativi e assoluti: FDI rispetto a FCM. Rischio con FCM = rischio grezzo aggregato dei bracci FCM "
         "dei trial nella stima.", "",
         "| Esito | Finestra | Trial (partecipanti) | Rischio con FCM | Rischio con FDI | Differenza per 1000 [IC 95%] | Effetto relativo [IC 95%] | Certezza | Sintesi |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(g, key=lambda r: (r["esito"], r["finestra"] != "primaria")):
        rows = pr[(r["esito"], r["finestra"])]
        rel, assoluti = [], []
        for p in rows:
            if p["stima"]:
                rel.append(f"{p['misura']} {fmt(p['stima'])} [{fmt(p['ic_inf'])}; {fmt(p['ic_sup'])}]")
            if p.get("diff_1000"):
                assoluti.append(f"{p['diff_1000']} [{p['diff_1000_inf']}; {p['diff_1000_sup']}] ({p['misura']})")
        p0 = rows[0]
        if not rel:
            ts = [t for t in singoli if (t["esito"], t["finestra"]) == (r["esito"], r["finestra"])]
            rel = ["non aggregato: " + "; ".join(f"{t['trial']} {t['eventi_fdi']} vs {t['eventi_fcm']}" for t in ts)]
        # con più misure principali (es. S1: OR e RD) il rischio FCM dipende dai trial di ciascun modello
        piu = len([p for p in rows if p.get("rischio_fcm_1000")]) > 1
        cr = "; ".join(f"{p['rischio_fcm_1000']} per 1000" + (f" ({p['misura']})" if piu else "")
                       for p in rows if p.get("rischio_fcm_1000"))
        fdi = "; ".join(f"{p['rischio_fdi_1000']} per 1000" + (f" ({p['misura']})" if piu else "")
                        for p in rows if p.get("rischio_fdi_1000"))
        kn = "; ".join(f"{p['k']} ({p['partecipanti']})" + (f" ({p['misura']})" if len(rows) > 1 else "") for p in rows)
        s.append(f"| {ESITI.get(r['esito'], r['esito'])} | {r['finestra']} | {kn} | "
                 f"{cr} | {fdi} | {'; '.join(assoluti)} | "
                 f"{'; '.join(rel)} | {r['certezza']} | {r['frase']} |")
    for e in ("S5", "S8a"):
        if not any(x["esito"] == e for x in g):
            s.append(f"| {ESITI[e]} | — | 0 | | | | | nessuna-evidenza | Nessun RCT testa a testa riporta l'esito. |")

    m = ["---", "tipo: meta-analisi", "descrizione: giudizi GRADE motivati, generati da scripts/grade_meta.py --sof",
         "---", "", "# GRADE — giudizi motivati", "",
         "Guida: [[grade-meta]]. Dati: `50-Metanalisi/grade.csv` e `50-Metanalisi/output/`.", ""]
    for r in sorted(g, key=lambda r: (r["esito"], r["finestra"] != "primaria")):
        m += [f"## {r['esito']} — {ESITI.get(r['esito'], '')}, finestra {r['finestra']}", "",
              f"Certezza: **{r['certezza']}**. {r['frase']}", "",
              "| Dominio | Punteggio | Motivazione |", "|---|---|---|"]
        m += [f"| {NOMI[d]} | {r[d]} | {r['motivo_' + d]} |" for d in DOMINI]
        m.append("")
    return "\n".join(s) + "\n", "\n".join(m)


def sof() -> None:
    t_sof, t_grade = testi_sof()
    (MA / "sof.md").write_text(t_sof, encoding="utf-8")
    (MA / "grade.md").write_text(t_grade, encoding="utf-8")
    print("scritti 50-Metanalisi/sof.md e 50-Metanalisi/grade.md")


def main() -> None:
    ap = argparse.ArgumentParser(description="GRADE della meta-analisi")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--valida", metavar="FILE")
    g.add_argument("--confronta", nargs=2, metavar=("A", "B"))
    g.add_argument("--unisci", metavar="FILE")
    g.add_argument("--sof", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.valida:
        err = valida(args.valida)
        print("\n".join(err) if err else "valido")
        sys.exit(1 if err else 0)
    elif args.confronta:
        confronta(*args.confronta, args.out)
    elif args.unisci:
        unisci(args.unisci)
    else:
        sof()


if __name__ == "__main__":
    main()
