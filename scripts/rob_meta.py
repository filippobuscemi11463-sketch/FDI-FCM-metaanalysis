#!/usr/bin/env python3
"""RoB 2 della meta-analisi (99-Meta/rob2-meta.md; protocollo §10).

    python3 scripts/rob_meta.py --init
    python3 scripts/rob_meta.py --valida FILE.csv
    python3 scripts/rob_meta.py --confronta A.csv B.csv [--out diff.md]
    python3 scripts/rob_meta.py --unisci CONSENSO.csv

--valida ricalcola il giudizio di ogni dominio dalle risposte alle domande
guida (algoritmi di rob2-meta.md §3) e segnala i giudizi che non lo seguono,
salvo nota che cominci con «scostamento:».
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from common import DIR_DATI

ROB = DIR_DATI / "ma-rob2.csv"
BRACCI = DIR_DATI / "ma-bracci.csv"
DOMINI = ["d1", "d2", "d3", "d4", "d5"]
COL = (["trial_id", "esito", "effetto"]
       + [c for d in DOMINI for c in (f"{d}_sq", d, f"{d}_supporto")]
       + ["complessivo", "valutatore", "note"])
GIUDIZI = ["basso", "alcune-preoccupazioni", "alto"]
RISPOSTE = {"Y", "PY", "PN", "N", "NI", "NA"}


def sq(testo: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"(\d\.\d)\s+(Y|PY|PN|N|NI|NA)\b", testo or ""):
        out[m.group(1)] = m.group(2)
    return out


def _in(v: str | None, *ammessi: str) -> bool:
    return v in ammessi


def algoritmo(d: str, a: dict[str, str]) -> str | None:
    """Giudizio atteso dal dominio d date le risposte a. None se mancano
    risposte necessarie."""
    g = a.get
    yes, no = ("Y", "PY"), ("N", "PN")
    if d == "d1":
        if not all(k in a for k in ("1.1", "1.2", "1.3")):
            return None
        if _in(g("1.2"), *no) or (g("1.2") == "NI" and _in(g("1.3"), *yes)):
            return "alto"
        if _in(g("1.1"), *yes, "NI") and _in(g("1.2"), *yes) and _in(g("1.3"), *no, "NI"):
            return "basso"
        return "alcune-preoccupazioni"
    if d == "d2":
        if "2.6" not in a:
            return None
        if (_in(g("2.4"), *yes) and _in(g("2.5"), *no, "NI")) or _in(g("2.7"), *yes):
            return "alto"
        consapevoli = not (_in(g("2.1"), *no) and _in(g("2.2"), *no))
        if (not consapevoli or _in(g("2.3"), *no)) and _in(g("2.6"), *yes):
            return "basso"
        return "alcune-preoccupazioni"
    if d == "d3":
        if "3.1" not in a:
            return None
        if _in(g("3.1"), *yes) or _in(g("3.2"), *yes) or _in(g("3.3"), *no):
            return "basso"
        if _in(g("3.4"), *yes):
            return "alto"
        return "alcune-preoccupazioni"
    if d == "d4":
        if not all(k in a for k in ("4.1", "4.2", "4.3")):
            return None
        if _in(g("4.1"), *yes) or _in(g("4.2"), *yes) or _in(g("4.5"), *yes, "NI"):
            return "alto"
        if (_in(g("4.1"), *no, "NI") and _in(g("4.2"), *no)
                and (_in(g("4.3"), *no) or _in(g("4.4"), *no))):
            return "basso"
        return "alcune-preoccupazioni"
    if d == "d5":
        if not all(k in a for k in ("5.1", "5.2", "5.3")):
            return None
        if _in(g("5.2"), *yes) or _in(g("5.3"), *yes):
            return "alto"
        if _in(g("5.1"), *yes) and _in(g("5.2"), *no) and _in(g("5.3"), *no):
            return "basso"
        return "alcune-preoccupazioni"
    return None


def leggi(path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        if (r.fieldnames or []) != COL:
            sys.exit(f"{path}: intestazione diversa da quella attesa:\n{','.join(COL)}")
        return list(r)


def valida(path) -> list[str]:
    rows = leggi(path)
    usati = set()
    with open(BRACCI, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["usa_in_analisi"] == "si":
                usati.add((r["trial_id"], r["esito"]))
    err = []
    for i, r in enumerate(rows, 2):
        dove = f"riga {i} ({r['trial_id']} {r['esito']})"
        if (r["trial_id"], r["esito"]) not in usati:
            err.append(f"{dove}: combinazione senza righe usate in ma-bracci.csv")
        if r["effetto"] != "assegnazione":
            err.append(f"{dove}: effetto deve essere «assegnazione»")
        if r["valutatore"] not in {"A", "B", "consenso"}:
            err.append(f"{dove}: valutatore fuori dominio")
        scost = "scostamento:" in r["note"].lower()
        livelli = []
        for d in DOMINI:
            if r[d] not in GIUDIZI:
                err.append(f"{dove}: {d}={r[d]!r} fuori dominio")
                continue
            livelli.append(GIUDIZI.index(r[d]))
            a = sq(r[f"{d}_sq"])
            if not a:
                err.append(f"{dove}: {d}_sq vuoto o illeggibile")
            if any(v not in RISPOSTE for v in a.values()):
                err.append(f"{dove}: {d}_sq con risposta non ammessa")
            atteso = algoritmo(d, a)
            if atteso and atteso != r[d] and not scost:
                err.append(f"{dove}: {d}={r[d]} ma l'algoritmo dà {atteso} "
                           "(serve una nota «scostamento: …»)")
            if not r[f"{d}_supporto"].strip():
                err.append(f"{dove}: {d}_supporto vuoto")
        if r["complessivo"] not in GIUDIZI:
            err.append(f"{dove}: complessivo fuori dominio")
        elif livelli and GIUDIZI.index(r["complessivo"]) < max(livelli):
            err.append(f"{dove}: complessivo più favorevole del peggior dominio")
    return err


def confronta(pa, pb, out) -> None:
    a = {(r["trial_id"], r["esito"]): r for r in leggi(pa)}
    b = {(r["trial_id"], r["esito"]): r for r in leggi(pb)}
    righe = ["# Confronto RoB 2, A e B", "",
             f"Combinazioni: A {len(a)}, B {len(b)}, comuni {len(set(a) & set(b))}.", ""]
    giudizi, risposte = [], []
    for k in sorted(set(a) & set(b)):
        for d in DOMINI + ["complessivo"]:
            if a[k][d] != b[k][d]:
                giudizi.append((k, d, a[k][d], b[k][d]))
        for d in DOMINI:
            sa, sb = sq(a[k][f"{d}_sq"]), sq(b[k][f"{d}_sq"])
            for q in sorted(set(sa) | set(sb)):
                if sa.get(q) != sb.get(q):
                    risposte.append((k, q, sa.get(q, "—"), sb.get(q, "—")))
    righe += [f"Giudizi discordanti: {len(giudizi)}. Risposte discordanti: {len(risposte)}.", ""]
    if giudizi:
        righe += ["## Giudizi discordanti", "", "| Trial | Esito | Dominio | A | B |", "|---|---|---|---|---|"]
        righe += [f"| {k[0]} | {k[1]} | {d} | {x} | {y} |" for k, d, x, y in giudizi] + [""]
    if risposte:
        righe += ["## Risposte discordanti", "", "| Trial | Esito | Domanda | A | B |", "|---|---|---|---|---|"]
        righe += [f"| {k[0]} | {k[1]} | {q} | {x} | {y} |" for k, q, x, y in risposte] + [""]
    for nome, s in (("Solo in A", set(a) - set(b)), ("Solo in B", set(b) - set(a))):
        if s:
            righe += [f"## {nome}", ""] + [f"- {k[0]} {k[1]}" for k in sorted(s)] + [""]
    testo = "\n".join(righe)
    if out:
        Path(out).write_text(testo, encoding="utf-8")
    print(testo)


def unisci(path) -> None:
    err = valida(path)
    if err:
        sys.exit("Validazione fallita:\n  " + "\n  ".join(err))
    rows = leggi(path)
    if any(r["valutatore"] != "consenso" for r in rows):
        sys.exit("Si uniscono solo righe di consenso")
    gia = {(r["trial_id"], r["esito"]) for r in leggi(ROB)}
    doppie = [(r["trial_id"], r["esito"]) for r in rows if (r["trial_id"], r["esito"]) in gia]
    if doppie:
        sys.exit(f"Già presenti: {doppie}")
    with open(ROB, "a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=COL).writerows(rows)
    print(f"{len(rows)} righe aggiunte a {ROB.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="RoB 2 della meta-analisi")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--init", action="store_true")
    g.add_argument("--valida", metavar="FILE")
    g.add_argument("--confronta", nargs=2, metavar=("A", "B"))
    g.add_argument("--unisci", metavar="FILE")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.init:
        if ROB.exists():
            print("ma-rob2.csv esiste già")
        else:
            with open(ROB, "w", encoding="utf-8", newline="") as fh:
                csv.writer(fh).writerow(COL)
            print("creato 30-Dati/ma-rob2.csv")
    elif args.valida:
        err = valida(args.valida)
        print("\n".join(err) if err else "valido")
        sys.exit(1 if err else 0)
    elif args.confronta:
        confronta(*args.confronta, args.out)
    else:
        unisci(args.unisci)


if __name__ == "__main__":
    main()
