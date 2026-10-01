#!/usr/bin/env python3
"""Build the public data repository of the FDI vs FCM meta-analysis from the
private vault. Copies only meta-analysis material; never copies full texts,
abstracts, PDFs or database backups. The database is exported as CSV without
the abstract column. Run from anywhere: build_public.py VAULT DEST."""
import csv, shutil, sqlite3, subprocess, sys
from pathlib import Path

VAULT, DEST = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()

FILES = [
    "CLAUDE.md",  # analisi.R checks for it to locate the repository root
    "30-Dati/ma-bracci.csv", "30-Dati/ma-trial.csv", "30-Dati/ma-rob2.csv",
    "99-Meta/protocollo-metanalisi.md",
    "99-Meta/criteri-screening-meta.md", "99-Meta/estrazione-meta.md",
    "99-Meta/rob2-meta.md", "99-Meta/grade-meta.md",
    "99-Meta/ricerca-manuale-meta.md", "99-Meta/queries.yaml",
    "99-Meta/log/ma-ricerca-2026-09-29.md",
    "99-Meta/log/querytranslation-M1-rct-head-to-head-2026-09-29.txt",
    "99-Meta/log/fonti-meta-2026-09-29.json",
    "99-Meta/log/fonti-meta-altri-metodi-2026-09-29.json",
    "99-Meta/log/fonti-meta-citazioni-doi-2026-09-29.json",
    "99-Meta/log/fonti-meta-consensus-2026-09-29.json",
    "99-Meta/log/citazioni-meta-2026-09-29.json",
    "99-Meta/log/fase2-da-recuperare-2026-09-29.md",
    "99-Meta/log/fact-check-manoscritto-2026-09-29.md",
    "60-Manoscritti/revisione-sistematica/main.tex",
    "60-Manoscritti/revisione-sistematica/main.pdf",
    "60-Manoscritti/revisione-sistematica/prisma-checklist.tex",
    "60-Manoscritti/revisione-sistematica/prisma-checklist.pdf",
    "60-Manoscritti/revisione-sistematica/descrittori-en.csv",
    "60-Manoscritti/revisione-sistematica/doi-riferimenti.csv",
    "60-Manoscritti/revisione-sistematica/generati/numeri.tex",
    "60-Manoscritti/revisione-sistematica/generati/refs-trial.bib",
    "60-Manoscritti/revisione-sistematica/generati/refs-altri.bib",
    "60-Manoscritti/revisione-sistematica/generati/tab-caratteristiche.tex",
    "60-Manoscritti/revisione-sistematica/generati/tab-rob.tex",
    "60-Manoscritti/revisione-sistematica/generati/tab-sof.tex",
    "scripts/common.py", "scripts/db.py", "scripts/pubmed_harvest.py",
    "scripts/fonti_meta.py", "scripts/citazioni_meta.py", "scripts/sorgenti_meta.py",
    "scripts/export_meta.py", "scripts/screening_meta.py", "scripts/estrazione_meta.py",
    "scripts/rob_meta.py", "scripts/grade_meta.py", "scripts/manoscritto_meta.py",
    "scripts/requirements.txt",
    ".claude/agents/meta-screener.md", ".claude/agents/meta-eleggibilita.md",
    ".claude/agents/meta-estrattore.md", ".claude/agents/meta-rob2.md",
    ".claude/agents/meta-grade.md",
]
DIRS = ["50-Metanalisi", "99-Meta/log/screening-meta", "99-Meta/log/eleggibilita",
        "99-Meta/log/estrazione", "99-Meta/log/rob2", "99-Meta/log/grade"]
FROZEN = ("60-Manoscritti/registrazione-osf/protocollo-v1.0-fc19a3a.md",
          "99-Meta/protocollo-metanalisi-v1.0-fc19a3a.md")

for rel in FILES:
    dst = DEST / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VAULT / rel, dst)
for rel in DIRS:
    shutil.copytree(VAULT / rel, DEST / rel, dirs_exist_ok=True)
(DEST / FROZEN[1]).parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(VAULT / FROZEN[0], DEST / FROZEN[1])

# Database export: meta-analysis records only, no abstracts.
out = DEST / "99-Meta/db"
out.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(f"file:{VAULT / '99-Meta/state.sqlite'}?mode=ro", uri=True)
META = "corpus IN ('meta','wiki+meta')"
COLS = ["pmid", "doi", "pmcid", "titolo", "autori", "anno", "rivista", "pubtypes",
        "lingua", "corpus", "primo_harvest", "stato_screening_meta",
        "motivo_screening_meta", "stato_eleggibilita_meta", "motivo_eleggibilita_meta"]

def dump(name, sql, header):
    with open(out / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(con.execute(sql))

dump("record-meta.csv", f"SELECT {','.join(COLS)} FROM record WHERE {META} ORDER BY pmid",
     ["id" if c == "pmid" else c for c in COLS])
dump("record-query-meta.csv",
     f"SELECT q.pmid, q.query FROM record_query q JOIN record r ON r.pmid=q.pmid "
     f"WHERE r.{META} ORDER BY 1,2", ["id", "query"])
dump("trial.csv", "SELECT trial_id, acronimo, altri_registri, note FROM trial ORDER BY 1",
     ["trial_id", "acronimo", "altri_registri", "note"])
dump("trial-pubblicazione.csv",
     "SELECT trial_id, pmid, ruolo, note FROM trial_pubblicazione ORDER BY 1,2",
     ["trial_id", "id", "ruolo", "note"])

# Provenance: history of the meta-analysis files in the private vault
# (hash, date, subject; no author e-mails).
paths = ["99-Meta/protocollo-metanalisi.md", "99-Meta/criteri-screening-meta.md",
         "99-Meta/estrazione-meta.md", "99-Meta/rob2-meta.md", "99-Meta/grade-meta.md",
         "30-Dati/ma-bracci.csv", "30-Dati/ma-trial.csv", "30-Dati/ma-rob2.csv",
         "50-Metanalisi", "60-Manoscritti/revisione-sistematica/main.tex",
         "99-Meta/log/screening-meta", "99-Meta/log/eleggibilita",
         "99-Meta/log/estrazione", "99-Meta/log/rob2", "99-Meta/log/grade"]
log = subprocess.run(["git", "-C", str(VAULT), "log", "--date=iso-strict",
                      "--format=%H%x09%ad%x09%s", "--", *paths],
                     capture_output=True, text=True, check=True).stdout
(DEST / "99-Meta/log/git-history-private-vault.tsv").write_text(
    "commit\tdate\tsubject\n" + log, encoding="utf-8")
print("ok")
