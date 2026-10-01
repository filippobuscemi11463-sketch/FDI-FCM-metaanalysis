#!/usr/bin/env python3
"""Screening del corpus della meta-analisi (99-Meta/criteri-screening-meta.md).

Fase 1, titolo e abstract, con doppio passaggio indipendente del subagent
`meta-screener` (protocollo §8.2 e deviazione del 2026-09-29):

    python3 scripts/screening_meta.py --pending 25 --out blocco.json
    # due passaggi del meta-screener sullo stesso blocco → A.json, B.json
    python3 scripts/screening_meta.py --confronta A.json B.json

Le decisioni concordi vanno in DB; discordanze e `dubbio` diventano `dubbio`
con i due motivi affiancati, e le decide l'utente:

    python3 scripts/screening_meta.py --decidi PMID incluso "motivo"
    python3 scripts/screening_meta.py --decidi PMID escluso "E3-non-primario: …"

Fase 2, eleggibilità sul fulltext, sempre decisa dall'utente:

    python3 scripts/screening_meta.py --eleggibilita PMID incluso "motivo"
    python3 scripts/screening_meta.py --eleggibilita PMID in-attesa "A-protocollo: …"

Accordo fra i passaggi A e B su tutti i confronti registrati:

    python3 scripts/screening_meta.py --kappa
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime

from common import IN_META, LOG_DIR, connect, log_run, now_iso

DIR_LOG = LOG_DIR / "screening-meta"
STATI_TA = ("incluso", "escluso", "dubbio")
STATI_EL = ("incluso", "escluso", "dubbio", "in-attesa")
CODICI_TA = ("E1-non-randomizzato", "E2-manca-FDI-o-FCM", "E3-non-primario",
             "E4-non-umano", "E5-pediatrico", "E6-cosomministrazione", "E7-errata")
CODICI_EL = CODICI_TA + ("E9-quasi-randomizzato", "E10-popolazione", "E11-duplicato",
                         "E12-fulltext-irreperibile")
CODICI_ATTESA = ("A-protocollo", "A-senza-risultati")


def valida_motivo(stato: str, motivo: str, codici: tuple[str, ...]) -> str | None:
    """Ritorna un messaggio d'errore, oppure None se il motivo è valido."""
    motivo = motivo.strip()
    if not motivo:
        return "motivo obbligatorio"
    if stato == "escluso" and not motivo.startswith(codici):
        return f"un'esclusione comincia con un codice: {', '.join(codici)}"
    if stato == "in-attesa" and not motivo.startswith(CODICI_ATTESA):
        return f"'in-attesa' comincia con {' o '.join(CODICI_ATTESA)}"
    return None


# ------------------------------------------------------------------ fase 1
def pending(n: int, out: str | None) -> None:
    con = connect()
    rows = con.execute(
        f"""SELECT pmid, titolo, anno, rivista, pubtypes, abstract FROM record
            WHERE {IN_META} AND stato_screening_meta IS NULL
            ORDER BY pmid LIMIT ?""", (n,)).fetchall()
    con.close()
    blocco = [{"pmid": r["pmid"], "titolo": r["titolo"], "anno": r["anno"],
               "rivista": r["rivista"], "pubtypes": r["pubtypes"],
               "abstract": (r["abstract"] or "")[:4000]} for r in rows]
    testo = json.dumps(blocco, ensure_ascii=False, indent=1)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(testo + "\n")
    else:
        print(testo)
    rest = connect().execute(
        f"SELECT COUNT(*) FROM record WHERE {IN_META} AND stato_screening_meta IS NULL"
    ).fetchone()[0]
    print(f"({len(blocco)} record nel blocco; {rest} ancora da valutare in fase 1)",
          file=sys.stderr)


def leggi(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as fh:
        dati = json.load(fh)
    out: dict[str, dict] = {}
    for d in dati:
        pmid = str(d.get("pmid", "")).strip()
        dec = str(d.get("decisione", "")).strip().lower()
        motivo = str(d.get("motivo", "")).strip()
        if dec not in STATI_TA:
            sys.exit(f"{path}: {pmid}: decisione '{dec}' non ammessa")
        err = valida_motivo(dec, motivo, CODICI_TA)
        if err:
            sys.exit(f"{path}: {pmid}: {err}")
        if pmid in out:
            sys.exit(f"{path}: {pmid} ripetuto")
        out[pmid] = {"decisione": dec, "motivo": motivo}
    return out


def unisci(a: dict, b: dict) -> tuple[str, str]:
    da, db = a["decisione"], b["decisione"]
    if da == db and da != "dubbio":
        # Per un'esclusione concorde il motivo comincia con il codice di A: il
        # PRISMA raggruppa per prefisso. Il codice di B resta nel testo.
        return da, f"{a['motivo']} ‖ B: {b['motivo']}"
    etichetta = "DISCORDANZA" if da != db else "DUBBIO"
    return "dubbio", f"{etichetta} — A={da}: {a['motivo']} ‖ B={db}: {b['motivo']}"


def confronta(path_a: str, path_b: str, forza: bool) -> None:
    a, b = leggi(path_a), leggi(path_b)
    if set(a) != set(b):
        sys.exit(f"A e B non hanno gli stessi PMID: solo A {sorted(set(a) - set(b))}, "
                 f"solo B {sorted(set(b) - set(a))}")
    con = connect()
    for pmid in a:
        r = con.execute(f"SELECT stato_screening_meta s FROM record "
                        f"WHERE pmid=? AND {IN_META}", (pmid,)).fetchone()
        if r is None:
            sys.exit(f"{pmid}: non è nel corpus della meta-analisi")
        if r["s"] is not None and not forza:
            sys.exit(f"{pmid}: già deciso ({r['s']}); usa --forza per sovrascrivere")

    # I grezzi si conservano prima di scrivere: sono la prova del doppio screening.
    DIR_LOG.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    for lettera, dati in (("A", a), ("B", b)):
        dest = DIR_LOG / f"{ts}-{lettera}.json"
        dest.write_text(json.dumps([{"pmid": p, **d} for p, d in dati.items()],
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    esiti: Counter = Counter()
    for pmid in a:
        stato, motivo = unisci(a[pmid], b[pmid])
        con.execute("UPDATE record SET stato_screening_meta=?, motivo_screening_meta=?, "
                    "ultimo_aggiornamento=? WHERE pmid=?", (stato, motivo, now_iso(), pmid))
        esiti[stato] += 1
    con.commit()
    con.close()
    k, po = kappa([(a[p]["decisione"], b[p]["decisione"]) for p in a])
    print(f"Fase 1: {len(a)} record — " + ", ".join(f"{s} {n}" for s, n in esiti.items()))
    print(f"Accordo A/B su questo blocco: {po:.1%} osservato, kappa di Cohen {k:.2f}")
    print(f"Grezzi salvati in {DIR_LOG.relative_to(LOG_DIR.parent.parent)}/{ts}-[AB].json")
    if esiti["dubbio"]:
        print(f"→ {esiti['dubbio']} dubbi da decidere con --decidi")
    log_run("screening_meta", "confronta", "ok",
            f"{len(a)} record, {dict(esiti)}, kappa {k:.2f}, grezzi {ts}")


def kappa(coppie: list[tuple[str, str]]) -> tuple[float, float]:
    n = len(coppie)
    if not n:
        return float("nan"), float("nan")
    po = sum(x == y for x, y in coppie) / n
    ca, cb = Counter(x for x, _ in coppie), Counter(y for _, y in coppie)
    pe = sum(ca[c] * cb[c] for c in STATI_TA) / n ** 2
    return ((po - pe) / (1 - pe) if pe < 1 else 1.0), po


def kappa_totale() -> None:
    coppie = []
    for fa in sorted(DIR_LOG.glob("*-A.json")):
        fb = fa.with_name(fa.name.replace("-A.json", "-B.json"))
        a = {d["pmid"]: d["decisione"] for d in json.loads(fa.read_text(encoding="utf-8"))}
        b = {d["pmid"]: d["decisione"] for d in json.loads(fb.read_text(encoding="utf-8"))}
        coppie += [(a[p], b[p]) for p in a]
    k, po = kappa(coppie)
    print(f"{len(coppie)} decisioni appaiate: accordo osservato {po:.1%}, kappa {k:.2f}")
    tab = Counter(coppie)
    for x in STATI_TA:
        print("  A=" + f"{x:<8}" + "  ".join(f"B={y}:{tab[(x, y)]:>4}" for y in STATI_TA))


# ------------------------------------------------------- decisioni dell'utente
def decidi(fase: str, pmid: str, stato: str, motivo: str) -> None:
    colonna, stati, codici = (
        ("screening", STATI_TA, CODICI_TA) if fase == "ta"
        else ("eleggibilita", STATI_EL, CODICI_EL))
    if stato not in stati:
        sys.exit(f"stato '{stato}' non ammesso in questa fase: {', '.join(stati)}")
    err = valida_motivo(stato, motivo, codici)
    if err:
        sys.exit(err)
    con = connect()
    r = con.execute(f"SELECT stato_{colonna}_meta s, motivo_{colonna}_meta m FROM record "
                    f"WHERE pmid=? AND {IN_META}", (pmid,)).fetchone()
    if r is None:
        sys.exit(f"{pmid}: non è nel corpus della meta-analisi")
    try:
        con.execute(f"UPDATE record SET stato_{colonna}_meta=?, motivo_{colonna}_meta=?, "
                    "ultimo_aggiornamento=? WHERE pmid=?",
                    (stato, motivo.strip(), now_iso(), pmid))
    except Exception as exc:  # noqa: BLE001 — il CHECK del DB spiega il perché
        sys.exit(f"{pmid}: rifiutato dal DB ({exc})")
    con.commit()
    con.close()
    prima = f"{r['s']} → " if r["s"] else ""
    print(f"{pmid}: {colonna} {prima}{stato}")
    log_run("screening_meta", f"decidi-{fase}", "ok",
            f"{pmid}: {r['s']} -> {stato}; {motivo.strip()}; prima: {r['m'] or ''}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Screening della meta-analisi")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pending", type=int, metavar="N")
    g.add_argument("--confronta", nargs=2, metavar=("A.json", "B.json"))
    g.add_argument("--decidi", nargs=3, metavar=("PMID", "STATO", "MOTIVO"))
    g.add_argument("--eleggibilita", nargs=3, metavar=("PMID", "STATO", "MOTIVO"))
    g.add_argument("--kappa", action="store_true")
    ap.add_argument("--out", help="con --pending: scrive il blocco in questo file")
    ap.add_argument("--forza", action="store_true",
                    help="con --confronta: sovrascrive decisioni già presenti")
    args = ap.parse_args()

    if args.pending:
        pending(args.pending, args.out)
    elif args.confronta:
        confronta(*args.confronta, args.forza)
    elif args.decidi:
        decidi("ta", *args.decidi)
    elif args.eleggibilita:
        decidi("el", *args.eleggibilita)
    else:
        kappa_totale()


if __name__ == "__main__":
    main()
