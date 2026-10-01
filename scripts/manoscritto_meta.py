#!/usr/bin/env python3
"""Numeri, tabelle, diagramma PRISMA e bibliografia dei trial per il manoscritto
della revisione sistematica (60-Manoscritti/revisione-sistematica/).

    python3 scripts/manoscritto_meta.py            # numeri.tex, prisma.tex, tabelle
    python3 scripts/manoscritto_meta.py --bib      # anche refs-trial.bib (Crossref, con cache)

Nel testo LaTeX non si scrivono numeri a mano: si usano le macro \\val{chiave}
definite in generati/numeri.tex. Le fonti sono solo: state.sqlite (corpus meta),
99-Meta/log/ma-ricerca-2026-09-29.md (record identificati per fonte, che il DB
non conserva), 30-Dati/ma-*.csv e 50-Metanalisi/ (output dello script R e GRADE).
Le fonti ancora da interrogare (Embase, CENTRAL, ICTRP) diventano segnaposto
evidenziati.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from common import DIR_DATI, VAULT_ROOT, connect

MS = VAULT_ROOT / "60-Manoscritti" / "revisione-sistematica"
GEN = MS / "generati"
MA_OUT = VAULT_ROOT / "50-Metanalisi" / "output"
LOG_RICERCA = VAULT_ROOT / "99-Meta" / "log" / "ma-ricerca-2026-09-29.md"
DESCRITTORI = MS / "descrittori-en.csv"

FONTI_DB = {"M1-rct-head-to-head": "pubmed", "S-europepmc": "epmc", "S-ctgov": "ctgov",
            "S-euctr": "euctr", "S-crossref": "crossref"}
FONTI_ALTRE = {"S-citazioni": "citazioni", "S-consensus": "consensus", "S-altri-metodi": "altri"}
VOLUME_DERIVATO = re.compile(r"^EPMC-PMC\d+-")
ESITI_EN = {"P1": "Hypophosphataemia ($<$0.65 mmol/L)", "S1": "Severe hypophosphataemia ($\\le$0.32 mmol/L)",
            "S2": "Hypophosphataemia, wide threshold ($<$0.80 mmol/L)", "S3": "Persistent hypophosphataemia",
            "S4": "Change in serum phosphate (mmol/L)", "S5": "Osteomalacia and fractures",
            "S6": "Serious or severe hypersensitivity", "S7": "Any hypersensitivity or infusion reaction",
            "S8a": "Adjudicated cardiovascular events", "S8b": "Serious cardiac and vascular adverse events"}
CERTEZZA_EN = {"alta": "High", "moderata": "Moderate", "bassa": "Low", "molto-bassa": "Very low"}
FINESTRA_EN = {"primaria": "primary", "estesa": "extended"}
ROB_EN = {"basso": "Low", "alcune-preoccupazioni": "Some concerns", "alto": "High"}
ROB_SIMBOLO = {"basso": "\\robL", "alcune-preoccupazioni": "\\robS", "alto": "\\robH"}

valori: dict[str, str] = {}


def V(chiave: str, valore) -> None:
    if chiave in valori and valori[chiave] != str(valore):
        sys.exit(f"chiave duplicata con valori diversi: {chiave}")
    valori[chiave] = str(valore)


def fmt(x, cifre: int = 2) -> str:
    """Numero in notazione inglese: due decimali, due cifre significative sotto 0,1."""
    if x in ("", None):
        return ""
    v = float(x)
    s = f"{v:.2g}" if v != 0 and abs(v) < 0.1 else f"{v:.{cifre}f}"
    return s.replace("-", "$-$")


def tex(s: str) -> str:
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
             .replace("_", "\\_").replace("#", "\\#").replace("$", "\\$"))


def leggi_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------ PRISMA
def riga_log(fonte: str) -> list[str]:
    for line in LOG_RICERCA.read_text(encoding="utf-8").splitlines():
        celle = [c.strip() for c in line.strip().strip("|").split("|")]
        if celle and celle[0].startswith(fonte):
            return celle
    sys.exit(f"{LOG_RICERCA.name}: nessuna riga per la fonte «{fonte}»")


def intero(cella: str, fonte: str) -> int:
    m = re.match(r"\s*(\d+)", cella)
    if not m:
        sys.exit(f"{LOG_RICERCA.name}: numero non leggibile per «{fonte}»: {cella!r}")
    return int(m.group(1))


def prisma() -> None:
    ident = {}
    for fonte, chiave in (("PubMed", "pubmed"), ("Europe PMC", "epmc"), ("ClinicalTrials.gov", "ctgov"),
                          ("EU CTR", "euctr"), ("EU CTIS", "ctis"), ("Crossref", "crossref")):
        celle = riga_log(fonte)
        ident[chiave] = intero(celle[3], fonte)
        V(f"prisma.ident.{chiave}", ident[chiave])
    V("prisma.ident.db", sum(ident.values()))
    pubmed_non_importati = ident["pubmed"] - intero(riga_log("PubMed")[4], "PubMed")
    V("prisma.removed.other", pubmed_non_importati)

    cit = riga_log("Ricerca per citazione")
    m = re.match(r"(\d+) identificativi, (\d+) non nel DB", cit[3])
    if not m:
        sys.exit("riga della ricerca per citazione non leggibile")
    V("prisma.cit.ident", m.group(1))
    V("prisma.cit.indb", int(m.group(1)) - int(m.group(2)))
    V("prisma.cit.notindb", m.group(2))
    V("prisma.cit.imported", intero(cit[4], "citazioni"))
    V("prisma.cit.outfilter", int(m.group(2)) - intero(cit[4], "citazioni"))
    cons = riga_log("Consensus")
    V("prisma.consensus.ident", intero(cons[3], "Consensus"))
    V("prisma.consensus.new", intero(cons[4], "Consensus"))

    con = connect()
    fonti = defaultdict(set)
    for r in con.execute("SELECT pmid, query FROM record_query"):
        fonti[r["pmid"]].add(r["query"])
    rows = list(con.execute(
        "SELECT pmid, stato_screening_meta s1, motivo_screening_meta m1, "
        "stato_eleggibilita_meta s2, motivo_eleggibilita_meta m2 FROM record "
        "WHERE corpus IN ('meta', 'wiki+meta')"))
    n_trial = con.execute("SELECT COUNT(*) FROM trial").fetchone()[0]
    con.close()

    ramo = {}
    for r in rows:
        q = fonti[r["pmid"]]
        ramo[r["pmid"]] = "db" if q & set(FONTI_DB) else "altri"
    for b in ("db", "altri"):
        rr = [r for r in rows if ramo[r["pmid"]] == b]
        derivati = [r for r in rr if VOLUME_DERIVATO.match(r["pmid"])]
        screenati = [r for r in rr if not VOLUME_DERIVATO.match(r["pmid"])]
        if any(r["s1"] is None for r in screenati):
            sys.exit(f"ramo {b}: record senza decisione di fase 1")
        escl1 = [r for r in screenati if r["s1"] == "escluso"]
        cercati = [r for r in rr if r["s1"] == "incluso"]
        non_recuperati = [r for r in cercati if (r["m2"] or "").startswith("E12-")]
        valutati = [r for r in cercati if not (r["m2"] or "").startswith("E12-")]
        escl2 = [r for r in valutati if r["s2"] == "escluso"]
        attesa = [r for r in valutati if r["s2"] == "in-attesa"]
        incl = [r for r in valutati if r["s2"] == "incluso"]
        if len(escl2) + len(attesa) + len(incl) != len(valutati):
            sys.exit(f"ramo {b}: record valutati senza decisione di fase 2")
        V(f"prisma.{b}.screened", len(screenati))
        V(f"prisma.{b}.excluded", len(escl1))
        V(f"prisma.{b}.derived", len(derivati))
        V(f"prisma.{b}.sought", len(cercati))
        V(f"prisma.{b}.notretrieved", len(non_recuperati))
        V(f"prisma.{b}.assessed", len(valutati))
        V(f"prisma.{b}.excluded2", len(escl2))
        V(f"prisma.{b}.awaiting", len(attesa))
        V(f"prisma.{b}.included", len(incl))
        for cod, n in Counter(re.match(r"(E\d+)-", r["m2"]).group(1) for r in escl2).items():
            V(f"prisma.{b}.excl.{cod}", n)
        for cod, n in Counter(re.match(r"(E\d+)-", r["m1"]).group(1) for r in escl1).items():
            V(f"prisma.{b}.excl1.{cod}", n)
    V("prisma.db.dup", int(valori["prisma.ident.db"]) - int(valori["prisma.removed.other"])
      - int(valori["prisma.db.screened"]))
    V("prisma.reports.included", int(valori["prisma.db.included"]) + int(valori["prisma.altri.included"]))
    V("prisma.trials.included", n_trial)
    # §11: trial registrati vs pubblicati (alternativa al funnel plot)
    con = connect()
    reg_trial = {r[0] for r in con.execute(
        "SELECT DISTINCT trial_id FROM trial_pubblicazione WHERE ruolo = 'registro'")}
    pubblicati = {r[0] for r in con.execute(
        "SELECT DISTINCT trial_id FROM trial_pubblicazione WHERE ruolo = 'primaria'")}
    attesa = [r[0] for r in con.execute(
        "SELECT pmid FROM record WHERE stato_eleggibilita_meta = 'in-attesa'")]
    con.close()
    V("reg.trials.withregistry", len(reg_trial))
    V("reg.trials.withregistry.published", len(reg_trial & pubblicati))
    V("reg.awaiting", len(attesa))
    V("reg.awaiting.ids", ", ".join(sorted(attesa)))
    if int(valori["prisma.altri.screened"]) != int(valori["prisma.cit.imported"]):
        sys.exit("record del ramo «altri metodi» diversi dagli importati della ricerca per citazione")


# ------------------------------------------------------------------ screening
def kappa() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    import io
    from contextlib import redirect_stdout
    import screening_meta
    buf = io.StringIO()
    sys.argv = ["screening_meta.py", "--kappa"]
    with redirect_stdout(buf):
        try:
            screening_meta.main()
        except SystemExit:
            pass
    m = re.search(r"(\d+) decisioni appaiate: accordo osservato ([\d.]+)%, kappa ([\d.]+)", buf.getvalue())
    if not m:
        sys.exit("output di screening_meta.py --kappa non leggibile")
    V("screen.pairs", m.group(1))
    V("screen.agree", m.group(2))
    V("screen.kappa", m.group(3))


# ------------------------------------------------------------------ risultati
def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def risultati() -> None:
    ris = leggi_csv(MA_OUT / "risultati.csv")
    for r in ris:
        base = f"{r['esito']}.{r['finestra']}.{slug(r['analisi'])}.{slug(r['modello'])}.{r['misura']}"
        if r["analisi"] == "principale":
            base = f"{r['esito']}.{r['finestra']}.{r['misura']}"
        for c in ("stima", "ic_inf", "ic_sup"):
            if r[c]:
                V(f"{base}.{c}", fmt(r[c]))
        for c in ("k", "partecipanti", "eventi_fdi", "eventi_fcm", "rischio_fcm_1000", "rischio_fdi_1000",
                  "diff_1000", "diff_1000_inf", "diff_1000_sup"):
            if r.get(c):
                V(f"{base}.{c}", r[c].replace("-", "$-$") if c.startswith("diff") else r[c])
        if r["i2"]:
            V(f"{base}.i2", f"{float(r['i2']):.0f}")
        if r["p"]:
            p = float(r["p"])
            V(f"{base}.p", "$<$0.001" if p < 0.001 else f"{p:.2g}" if p < 0.01 else f"{p:.2f}")
        if r["q"]:
            V(f"{base}.q", f"{float(r['q']):.2f}")
        if r["q_p"]:
            qp = float(r["q_p"])
            V(f"{base}.q_p", "$<$0.001" if qp < 0.001 else f"{qp:.2g}" if qp < 0.1 else f"{qp:.2f}")
        if r["tau2"]:
            V(f"{base}.tau2", fmt(r["tau2"], 3))
        if r["pi_inf"]:
            V(f"{base}.pi_inf", fmt(r["pi_inf"])); V(f"{base}.pi_sup", fmt(r["pi_sup"]))
    for r in leggi_csv(MA_OUT / "input-analisi.csv"):
        if r["soglia"]:
            V(f"soglia.{r['esito']}.{r['finestra']}.{slug(r['etichetta'])}", f"{float(r['soglia']):.2f}")
    for t in leggi_csv(MA_OUT / "trial-singoli.csv"):
        base = f"trial.{t['esito']}.{t['finestra']}.{slug(t['trial'])}"
        V(f"{base}.fdi", t["eventi_fdi"]); V(f"{base}.fcm", t["eventi_fcm"])
        for c in ("rr", "rr_inf", "rr_sup", "rd", "rd_inf", "rd_sup"):
            if t[c]:
                V(f"{base}.{c}", fmt(t[c]))
    g = leggi_csv(VAULT_ROOT / "50-Metanalisi" / "grade.csv")
    for r in g:
        V(f"grade.{r['esito']}.{r['finestra']}", CERTEZZA_EN[r["certezza"]].lower())
    run = (MA_OUT / "run.txt").read_text(encoding="utf-8")
    V("run.commit", re.search(r"Commit HEAD:\s*(\w+)", run).group(1))
    V("run.sha", re.search(r"SHA-256 di 30-Dati/ma-bracci.csv:\s*(\w+)", run).group(1)[:12])
    V("run.metafor", re.search(r"metafor_([\d.-]+)", run).group(1))
    V("run.lme4", re.search(r"lme4_([\d.-]+)", run).group(1))
    V("run.R", re.search(r"R version ([\d.]+)", run).group(1))


def trial_numeri() -> list[dict]:
    trial = leggi_csv(DIR_DATI / "ma-trial.csv")
    V("trials.n", len(trial))
    V("trials.rand.total", sum(int(t["n_randomizzati_totale"]) for t in trial))
    V("trials.rand.fdi", sum(int(t["n_randomizzati_fdi"]) for t in trial))
    V("trials.rand.fcm", sum(int(t["n_randomizzati_fcm"]) for t in trial))
    V("trials.pharmacosmos", sum(t["produttore_coinvolto"] == "pharmacosmos" for t in trial))
    V("trials.vifor", sum(t["produttore_coinvolto"] == "vifor" for t in trial))
    V("trials.indipendenti", sum(t["produttore_coinvolto"] == "nessuno" for t in trial))
    V("trials.openlabel", sum(t["cecita"] == "open-label" for t in trial))
    V("trials.doppio", sum(t["cecita"] == "doppio" for t in trial))
    desc = {d["trial_id"]: d for d in leggi_csv(DESCRITTORI)} if DESCRITTORI.exists() else {}
    V("trials.doppio.pieno", sum(desc.get(t["trial_id"], {}).get("cecita_en", "") == "Double-blind" for t in trial))
    V("trials.parziale", sum(desc.get(t["trial_id"], {}).get("cecita_en", "").startswith("Partially") for t in trial))
    bracci = leggi_csv(DIR_DATI / "ma-bracci.csv")
    # dati di ipofosfatemia non usati perché la soglia non è dichiarata (citati nel testo)
    for r in bracci:
        if (r["usa_in_analisi"] != "si" and r["soglia_testo"].startswith("non dichiarata")
                and r["n_eventi"] and r["n_analizzati"]):
            V(f"nonusato.{slug(r['trial_id'])}.{r['esito']}.{r['finestra']}.{r['farmaco']}",
              f"{r['n_eventi']}/{r['n_analizzati']}")
    V("rows.total", len(bracci))
    V("rows.used", sum(r["usa_in_analisi"] == "si" for r in bracci))
    rob = leggi_csv(DIR_DATI / "ma-rob2.csv")
    V("rob.n", len(rob))
    c = Counter(r["complessivo"] for r in rob)
    V("rob.some", c["alcune-preoccupazioni"]); V("rob.high", c["alto"]); V("rob.low", c["basso"])
    return trial


# ------------------------------------------------------------------ tabelle
def macro_tabella(nome: str, righe: list[str]) -> str:
    """Le righe finiscono in una macro: un \\input dentro tabularx rompe \\bottomrule."""
    return (f"% generato da scripts/manoscritto_meta.py — non modificare a mano\n"
            f"\\gdef\\{nome}{{%\n" + "\n".join(righe) + "\n}\n")


def chiave_bib(ident: str) -> str:
    return "R" + re.sub(r"[^A-Za-z0-9]", "", ident)


def tab_caratteristiche(trial: list[dict]) -> None:
    desc = {d["trial_id"]: d for d in leggi_csv(DESCRITTORI)}
    mancanti = [t["trial_id"] for t in trial if t["trial_id"] not in desc]
    if mancanti:
        sys.exit(f"{DESCRITTORI.name}: mancano i descrittori di {mancanti}")
    righe = []
    for t in sorted(trial, key=lambda t: desc[t["trial_id"]]["ordine"]):
        d = desc[t["trial_id"]]
        fu = t["follow_up_giorni"] or "NR"
        righe.append(
            f"{d['etichetta']} \\cite{{{chiave_bib(d['fonte_primaria'])}}} & {tex(d['paese_en'])} & {tex(d['popolazione_en'])} & "
            f"{tex(d['cecita_en'])} & {t['n_randomizzati_fdi']} / {t['n_randomizzati_fcm']} & "
            f"{tex(d['dose_fdi_en'])} & {tex(d['dose_fcm_en'])} & {fu} & {tex(d['finanziamento_en'])} \\\\")
    (GEN / "tab-caratteristiche.tex").write_text(macro_tabella("tabCaratteristiche", righe), encoding="utf-8")


def tab_rob() -> None:
    rob = leggi_csv(DIR_DATI / "ma-rob2.csv")
    desc = {d["trial_id"]: d for d in leggi_csv(DESCRITTORI)}
    righe = []
    for r in sorted(rob, key=lambda r: (desc[r["trial_id"]]["ordine"], r["esito"])):
        doms = " & ".join(ROB_SIMBOLO[r[d]] for d in ("d1", "d2", "d3", "d4", "d5"))
        righe.append(f"{desc[r['trial_id']]['etichetta']} & {r['esito']} & {doms} & "
                     f"{ROB_SIMBOLO[r['complessivo']]} \\\\")
    (GEN / "tab-rob.tex").write_text(macro_tabella("tabRob", righe), encoding="utf-8")


def tab_sof() -> None:
    g = leggi_csv(VAULT_ROOT / "50-Metanalisi" / "grade.csv")
    ris = [r for r in leggi_csv(MA_OUT / "risultati.csv") if r["analisi"] == "principale"]
    singoli = leggi_csv(MA_OUT / "trial-singoli.csv")
    desc = {d["trial_id"]: d for d in leggi_csv(DESCRITTORI)}
    righe = []
    for r in sorted(g, key=lambda r: (r["esito"], r["finestra"] != "primaria")):
        rows = [p for p in ris if (p["esito"], p["finestra"]) == (r["esito"], r["finestra"])]
        p0 = rows[0]
        rel = "; ".join(f"{p['misura']} {fmt(p['stima'])} ({fmt(p['ic_inf'])} to {fmt(p['ic_sup'])})"
                        for p in rows if p["stima"])
        ass = "; ".join(f"{p['diff_1000']} ({p['diff_1000_inf']} to {p['diff_1000_sup']})"
                        for p in rows if p.get("diff_1000")).replace("-", "$-$")
        piu = len([p for p in rows if p.get("rischio_fcm_1000")]) > 1
        cr = "; ".join(p["rischio_fcm_1000"] + (f" ({p['misura']})" if piu else "")
                       for p in rows if p.get("rischio_fcm_1000"))
        fdi = "; ".join(p["rischio_fdi_1000"] for p in rows if p.get("rischio_fdi_1000"))
        if not rel:
            ts = [t for t in singoli if (t["esito"], t["finestra"]) == (r["esito"], r["finestra"])]
            rel = "Not pooled: " + "; ".join(
                f"{desc[t['trial_id']]['etichetta']} {t['eventi_fdi']} vs {t['eventi_fcm']}" for t in ts)
        kn = "; ".join(f"{p['k']} ({p['partecipanti']})" + (f" ({p['misura']})" if len(rows) > 1 else "") for p in rows)
        righe.append(f"{ESITI_EN[r['esito']]}, {FINESTRA_EN[r['finestra']]} window & {kn} & "
                     f"{cr} & {fdi} & {ass} & {rel} & {CERTEZZA_EN[r['certezza']]} \\\\")
    for e in ("S5", "S8a"):
        righe.append(f"{ESITI_EN[e]} & 0 & & & & No head-to-head RCT reported this outcome & -- \\\\")
    (GEN / "tab-sof.tex").write_text(macro_tabella("tabSof", righe), encoding="utf-8")


# ------------------------------------------------------------------ bibliografia
def pulisci(t: str) -> str:
    """Titoli Crossref: via i tag HTML/JATS e gli spazi multipli."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()


def crossref(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "fdi-fcm-wiki"})
    try:
        with urllib.request.urlopen(req, timeout=30) as fh:
            m = json.load(fh)["message"]
    except Exception as e:  # noqa: BLE001
        m = {"errore": str(e)}
    time.sleep(0.3)
    return m


def bib() -> None:
    cache_p = GEN / "crossref-cache.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    con = connect()
    righe = list(con.execute(
        "SELECT DISTINCT tp.pmid, r.titolo, r.anno, r.rivista, r.doi FROM trial_pubblicazione tp "
        "JOIN record r USING (pmid)"))
    con.close()
    voci = []
    for r in righe:
        chiave = chiave_bib(r["pmid"])
        pmid = r["pmid"] if r["pmid"].isdigit() else ""
        doi = r["doi"] or ""
        if doi and doi not in cache:
            cache[doi] = crossref(doi)
        m = cache.get(doi, {}) if doi else {}
        if m and "errore" not in m:
            autori = " and ".join(
                f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") if a.get("family") else a.get("name", "")
                for a in m.get("author", [])) or "{Anonymous}"
            titolo = pulisci((m.get("title") or [r["titolo"]])[0])
            rivista = (m.get("container-title") or [r["rivista"] or ""])[0]
            anno = (m.get("issued", {}).get("date-parts") or [[r["anno"]]])[0][0]
            campi = {"author": autori, "title": "{" + titolo + "}", "journal": rivista, "year": anno,
                     "volume": m.get("volume", ""), "number": m.get("issue", ""), "pages": m.get("page", ""),
                     "doi": doi}
            tipo = "article"
        else:
            tipo = "misc"
            campi = {"title": "{" + (r["titolo"] or r["pmid"]) + "}", "howpublished": r["rivista"] or "",
                     "year": r["anno"] or "", "doi": doi}
            if r["pmid"].startswith("NCT"):
                campi["url"] = f"https://clinicaltrials.gov/study/{r['pmid']}"
            elif r["pmid"].startswith("EUCTR-"):
                campi["url"] = ("https://www.clinicaltrialsregister.eu/ctr-search/search?query="
                                + r["pmid"].removeprefix("EUCTR-"))
            elif r["pmid"].startswith("EPMC-"):
                pmc = re.match(r"EPMC-(PMC\d+|PPR\d+)", r["pmid"]).group(1)
                campi["url"] = f"https://europepmc.org/article/{'PMC' if pmc.startswith('PMC') else 'PPR'}/{pmc}"
        if pmid:
            campi["note"] = f"PMID {pmid}"
        corpo = ",\n".join(f"  {k} = {{{v}}}" if not str(v).startswith("{") else f"  {k} = {{{v}}}"
                           for k, v in campi.items() if v not in ("", None))
        voci.append(f"@{tipo}{{{chiave},\n{corpo}\n}}")
    (GEN / "refs-trial.bib").write_text("\n\n".join(voci) + "\n", encoding="utf-8")
    # metodi e revisioni precedenti: solo da DOI verificati su Crossref
    altre = []
    for d in leggi_csv(MS / "doi-riferimenti.csv"):
        m = cache.get(d["doi"]) or crossref(d["doi"])
        cache[d["doi"]] = m
        if "errore" in m:
            print(f"  DOI non risolto: {d['chiave']} {d['doi']}")
            continue
        autori = " and ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") if a.get("family")
                              else "{" + a.get("name", "") + "}" for a in m.get("author", []))
        campi = {"author": autori, "title": "{" + pulisci((m.get("title") or [""])[0]) + "}",
                 "journal": (m.get("container-title") or [""])[0],
                 "year": (m.get("issued", {}).get("date-parts") or [[""]])[0][0],
                 "volume": m.get("volume", ""), "number": m.get("issue", ""), "pages": m.get("page", ""),
                 "doi": d["doi"]}
        altre.append(f"@article{{{d['chiave']},\n" + ",\n".join(
            f"  {k} = {{{v}}}" for k, v in campi.items() if v not in ("", None)) + "\n}")
        print(f"  {d['chiave']:22} {campi['year']} {campi['title'][1:90]}")
    (GEN / "refs-altri.bib").write_text("\n\n".join(altre) + "\n", encoding="utf-8")
    cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    errori = [d for d, m in cache.items() if "errore" in m]
    print(f"refs-trial.bib: {len(voci)} voci; DOI non risolti su Crossref: {errori or 'nessuno'}")


# ------------------------------------------------------------------ scrittura
def scrivi_numeri() -> None:
    righe = ["% generato da scripts/manoscritto_meta.py — non modificare a mano",
             "\\makeatletter"]
    for k in sorted(valori):
        righe.append(f"\\@namedef{{val@{k}}}{{{valori[k]}}}")
    righe += ["\\makeatother", ""]
    (GEN / "numeri.tex").write_text("\n".join(righe), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Numeri e tabelle del manoscritto della revisione")
    ap.add_argument("--bib", action="store_true", help="rigenera anche refs-trial.bib da Crossref")
    args = ap.parse_args()
    GEN.mkdir(parents=True, exist_ok=True)
    prisma()
    kappa()
    risultati()
    trial = trial_numeri()
    scrivi_numeri()
    if DESCRITTORI.exists():
        tab_caratteristiche(trial)
        tab_rob()
        tab_sof()
    else:
        print(f"manca {DESCRITTORI.relative_to(VAULT_ROOT)}: tabelle non generate")
    if args.bib:
        bib()
    print(f"numeri.tex: {len(valori)} valori")


if __name__ == "__main__":
    main()
