#!/usr/bin/env python3
"""Validazione, confronto e unione delle estrazioni per braccio della
meta-analisi (99-Meta/estrazione-meta.md; protocollo §9).

    python3 scripts/estrazione_meta.py --init                 # crea i CSV vuoti
    python3 scripts/estrazione_meta.py --valida FILE.csv      # bracci o trial
    python3 scripts/estrazione_meta.py --confronta A.csv B.csv [--out diff.md]
    python3 scripts/estrazione_meta.py --unisci CONSENSO.csv  # in 30-Dati/

Il tipo di file (bracci o trial) si riconosce dall'intestazione.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from common import DIR_DATI, connect

BRACCI = DIR_DATI / "ma-bracci.csv"
TRIAL = DIR_DATI / "ma-trial.csv"

COL_BRACCI = ["trial_id", "pmid", "braccio", "farmaco", "dose_totale_mg", "schema",
              "n_randomizzati", "n_analizzati", "popolazione_analisi", "esito", "finestra",
              "soglia_mmol_l", "soglia_testo", "n_eventi", "percentuale", "media", "ds",
              "tipo_dispersione", "misura_continua", "unita", "tempo_misura_giorni",
              "pagina_o_tabella", "citazione", "fonte_dato", "estrattore", "usa_in_analisi",
              "note"]
COL_TRIAL = ["trial_id", "acronimo", "registri", "disegno", "cecita", "paese", "n_centri",
             "popolazione", "criterio_ferro", "criterio_fosfato_basale",
             "n_randomizzati_totale", "n_randomizzati_fdi", "n_randomizzati_fcm",
             "eta_media", "pct_donne", "dose_fdi", "dose_fcm", "follow_up_giorni",
             "esito_primario_registrato", "sponsor", "finanziamento", "produttore_coinvolto",
             "conflitti", "pmid_fonti", "pagina_o_tabella", "citazione", "estrattore", "note"]

DOMINI = {
    "farmaco": {"FDI", "FCM"},
    "popolazione_analisi": {"randomizzati", "safety", "itt", "mitt", "per-protocol", "altro"},
    "esito": {"P1", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8a", "S8b"},
    "finestra": {"primaria", "estesa"},
    "tipo_dispersione": {"", "ds", "es", "ic95", "iqr", "range"},
    "misura_continua": {"", "nadir", "variazione-da-basale", "valore-a-tempo"},
    "unita": {"", "mmol/L", "mg/dL"},
    "fonte_dato": {"fulltext", "supplementare", "registro", "abstract"},
    "estrattore": {"A", "B", "consenso"},
    "usa_in_analisi": {"", "si", "no"},
}
DOMINI_TRIAL = {
    "cecita": {"open-label", "singolo", "doppio", "non-riportato"},
    "finanziamento": {"industriale", "pubblico", "misto", "non-dichiarato", "nessuno"},
    "produttore_coinvolto": {"pharmacosmos", "vifor", "entrambi", "nessuno", "non-dichiarato"},
    "conflitti": {"si", "no", "non-dichiarati"},
    "estrattore": {"A", "B", "consenso"},
}
INTERI = ["n_randomizzati", "n_analizzati", "n_eventi"]
NUMERI = ["dose_totale_mg", "soglia_mmol_l", "percentuale", "media", "ds"]
CHIAVE = ["trial_id", "pmid", "farmaco", "esito", "finestra", "soglia_mmol_l",
          "misura_continua", "tempo_misura_giorni"]


def leggi(path: str | Path) -> tuple[str, list[dict]]:
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        rows = list(r)
        testa = r.fieldnames or []
    if testa == COL_BRACCI:
        return "bracci", rows
    if testa == COL_TRIAL:
        return "trial", rows
    sys.exit(f"{path}: intestazione non riconosciuta.\nattesa (bracci): {','.join(COL_BRACCI)}")


def valida(path: str | Path) -> list[str]:
    tipo, rows = leggi(path)
    con = connect()
    trial_db = {r[0] for r in con.execute("SELECT trial_id FROM trial")}
    legami = {(r[0], r[1]) for r in con.execute("SELECT trial_id, pmid FROM trial_pubblicazione")}
    con.close()
    err = []
    for i, r in enumerate(rows, 2):
        dove = f"riga {i}"
        if r["trial_id"] not in trial_db:
            err.append(f"{dove}: trial_id {r['trial_id']!r} non è nella tabella trial")
        if tipo == "trial":
            for c, dom in DOMINI_TRIAL.items():
                if r[c] not in dom:
                    err.append(f"{dove}: {c}={r[c]!r} fuori dominio {sorted(dom)}")
            continue
        if (r["trial_id"], r["pmid"]) not in legami:
            err.append(f"{dove}: {r['pmid']} non è collegato a {r['trial_id']} in trial_pubblicazione")
        for c, dom in DOMINI.items():
            if r[c] not in dom:
                err.append(f"{dove}: {c}={r[c]!r} fuori dominio {sorted(d for d in dom if d)}")
        for c in INTERI:
            if r[c] and not re.fullmatch(r"\d+", r[c]):
                err.append(f"{dove}: {c}={r[c]!r} non è un intero")
        for c in NUMERI:
            if r[c] and not re.fullmatch(r"-?\d+(\.\d+)?", r[c]):
                err.append(f"{dove}: {c}={r[c]!r} non è un numero (punto decimale)")
        if not r["pagina_o_tabella"] or not r["citazione"]:
            err.append(f"{dove}: pagina_o_tabella e citazione sono obbligatorie")
        continuo = r["esito"] == "S4"
        if continuo:
            if not (r["media"] and r["misura_continua"] and r["unita"]):
                err.append(f"{dove}: S4 richiede media, misura_continua e unita")
        else:
            if not r["n_eventi"] and not r["percentuale"]:
                err.append(f"{dove}: esito dicotomico senza n_eventi né percentuale")
            ignota = "non dichiarata" in r["soglia_testo"].lower()
            if r["esito"] in {"P1", "S1", "S2", "S3"} and not (r["soglia_mmol_l"] and r["soglia_testo"]):
                # Codebook §6.11: soglia non dichiarata dalla fonte → la riga resta,
                # ma non entra nell'analisi finché la soglia non si trova.
                if not ignota:
                    err.append(f"{dove}: {r['esito']} richiede soglia_mmol_l e soglia_testo "
                               "(oppure soglia_testo «non dichiarata»)")
                elif r["usa_in_analisi"] == "si":
                    err.append(f"{dove}: soglia non dichiarata, la riga non può essere usata")
        if r["n_eventi"] and r["n_analizzati"] and r["n_eventi"].isdigit() and r["n_analizzati"].isdigit():
            if int(r["n_eventi"]) > int(r["n_analizzati"]):
                err.append(f"{dove}: n_eventi > n_analizzati")
        if r["n_eventi"] and not r["n_analizzati"]:
            err.append(f"{dove}: n_eventi senza n_analizzati")
    return err


def chiave(r: dict) -> tuple:
    """Chiave di allineamento A/B. Oltre alle colonne di CHIAVE usa fonte_dato
    (fulltext e supplemento della stessa pubblicazione) e l'etichetta
    «sensibilità: …» della nota, normalizzata (analisi di sensibilità dello stesso
    esito). Etichette scritte in modo diverso da A e B finiscono in «solo A /
    solo B»: si vedono, non si perdono."""
    m = re.search(r"sensibilit[aà]\s*:\s*([^;.,«»]*)", r.get("note", ""), re.I)
    etichetta = re.sub(r"[^a-z0-9]", "", m.group(1).lower()) if m else ""
    return tuple(r[c] for c in CHIAVE) + (r.get("fonte_dato", ""), etichetta)


def confronta(pa: str, pb: str, out: str | None) -> None:
    ta, a = leggi(pa)
    tb, b = leggi(pb)
    if ta != tb:
        sys.exit("A e B non sono dello stesso tipo")
    k = chiave if ta == "bracci" else (lambda r: (r["trial_id"],))
    ia, ib = {}, {}
    for r in a:
        ia.setdefault(k(r), []).append(r)
    for r in b:
        ib.setdefault(k(r), []).append(r)
    ignora = {"estrattore", "citazione", "note", "braccio", "usa_in_analisi"}
    # Differenze di sola formulazione: si contano ma non si elencano fra le
    # discordanze di sostanza, che sono quelle da decidere in consenso.
    testuali = {"pagina_o_tabella", "schema", "soglia_testo", "popolazione", "dose_fdi",
                "dose_fcm", "criterio_ferro", "criterio_fosfato_basale", "pmid_fonti",
                "esito_primario_registrato", "sponsor", "disegno", "paese"}
    righe = ["# Confronto delle estrazioni A e B", "",
             f"A: `{pa}` ({len(a)} righe) — B: `{pb}` ({len(b)} righe)", ""]
    solo_a = sorted(set(ia) - set(ib))
    solo_b = sorted(set(ib) - set(ia))
    celle, testo = [], []
    for kk in sorted(set(ia) & set(ib)):
        if len(ia[kk]) != 1 or len(ib[kk]) != 1:
            celle.append((kk, "(chiave ripetuta)", f"{len(ia[kk])} righe", f"{len(ib[kk])} righe"))
            continue
        ra, rb = ia[kk][0], ib[kk][0]
        for c in ra:
            if c in ignora:
                continue
            if (ra[c] or "").strip() != (rb[c] or "").strip():
                (testo if c in testuali else celle).append((kk, c, ra[c], rb[c]))
    uguali = len(set(ia) & set(ib)) - len({c[0] for c in celle})
    righe += [f"Righe con la stessa chiave: {len(set(ia) & set(ib))}, concordi nella sostanza: {uguali}.",
              f"Solo in A: {len(solo_a)}. Solo in B: {len(solo_b)}. Discordanze di sostanza: "
              f"{len(celle)}. Differenze di sola formulazione: {len(testo)}.", ""]
    if celle:
        righe += ["## Discordanze di sostanza", "", "| Chiave | Colonna | A | B |", "|---|---|---|---|"]
        righe += [f"| {' / '.join(x for x in kk if x)} | {c} | {va} | {vb} |" for kk, c, va, vb in celle]
        righe.append("")
    if testo:
        righe += ["## Differenze di sola formulazione", "", "| Chiave | Colonna | A | B |", "|---|---|---|---|"]
        righe += [f"| {' / '.join(x for x in kk if x)} | {c} | {va[:80]} | {vb[:80]} |"
                  for kk, c, va, vb in testo]
        righe.append("")
    for titolo, lst, idx in (("Solo in A", solo_a, ia), ("Solo in B", solo_b, ib)):
        if lst:
            righe += [f"## {titolo}", ""]
            righe += [f"- {' / '.join(x for x in kk if x)} — {idx[kk][0].get('pagina_o_tabella', '')}"
                      for kk in lst]
            righe.append("")
    testo = "\n".join(righe)
    if out:
        Path(out).write_text(testo, encoding="utf-8")
        print(f"Confronto scritto in {out}")
    print("\n".join(righe[:7]))


def unisci(path: str) -> None:
    tipo, rows = leggi(path)
    err = valida(path)
    if err:
        sys.exit("Validazione fallita, niente unito:\n  " + "\n  ".join(err))
    if any(r["estrattore"] != "consenso" for r in rows):
        sys.exit("Si uniscono solo righe con estrattore = consenso")
    dest = BRACCI if tipo == "bracci" else TRIAL
    _, esistenti = leggi(dest)
    k = chiave if tipo == "bracci" else (lambda r: (r["trial_id"],))
    gia = {k(r) for r in esistenti}
    doppie = [k(r) for r in rows if k(r) in gia]
    if doppie:
        sys.exit(f"Righe già presenti in {dest.name}: {doppie[:5]}…")
    with open(dest, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COL_BRACCI if tipo == "bracci" else COL_TRIAL)
        w.writerows(rows)
    print(f"{len(rows)} righe aggiunte a {dest.relative_to(DIR_DATI.parent)}")


def init() -> None:
    for dest, col in ((BRACCI, COL_BRACCI), (TRIAL, COL_TRIAL)):
        if dest.exists():
            print(f"{dest.name} esiste già: non toccato")
            continue
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(col)
        print(f"creato {dest.relative_to(DIR_DATI.parent)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Estrazione per braccio della meta-analisi")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--init", action="store_true")
    g.add_argument("--valida", metavar="FILE")
    g.add_argument("--confronta", nargs=2, metavar=("A", "B"))
    g.add_argument("--unisci", metavar="FILE")
    ap.add_argument("--out", help="con --confronta: file markdown del confronto")
    args = ap.parse_args()
    if args.init:
        init()
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
