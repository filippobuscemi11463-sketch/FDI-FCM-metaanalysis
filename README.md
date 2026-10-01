# FDI vs FCM: head-to-head meta-analysis, data and code

Data, code and audit trail of the systematic review and meta-analysis

> **Ferric derisomaltose versus ferric carboxymaltose: a systematic review and meta-analysis of head-to-head randomised controlled trials on hypophosphataemia, osteomalacia, hypersensitivity and cardiovascular events**
> Filippo Buscemi, Primo Buscemi. Preprint (medRxiv, submitted).

The review was carried out in a private, version-controlled evidence repository that also holds the full texts of the included reports. This public repository is a snapshot of everything about the meta-analysis **except** the copyrighted sources: no full texts, no PDFs and no abstracts are redistributed. Commit hashes cited in the manuscript (for example `fc19a3a`, the frozen protocol) refer to that private repository. Their dates and subjects are listed in `99-Meta/log/git-history-private-vault.tsv`.

Working files are in Italian, the language of the project. A glossary is at the end.

## Reproducing the analysis

```bash
Rscript 50-Metanalisi/analisi.R      # run from the repository root
```

Requirements: R with `metafor` and `lme4`. The versions used are in `50-Metanalisi/output/run.txt`. The script reads only `30-Dati/ma-bracci.csv` (rows with `usa_in_analisi = si`), `30-Dati/ma-trial.csv`, `30-Dati/ma-rob2.csv` and `50-Metanalisi/sottogruppi.csv`, and rewrites `50-Metanalisi/output/`. Running it on this snapshot reproduces the published outputs (CSV files and forest plots) byte for byte. The only difference is the commit hash recorded in `run.txt`.

The manuscript compiles with `latexmk -pdf main.tex` in `60-Manoscritti/revisione-sistematica/`. Its numbers come only from `generati/numeri.tex`. In the working repository, `scripts/manoscritto_meta.py` generates that file from the selection database and the analysis outputs. The other Python scripts are included for transparency. They need the private database and do not run on this snapshot.

## Contents

| Path | What it is |
|---|---|
| `99-Meta/protocollo-metanalisi-v1.0-fc19a3a.md` | Protocol as frozen before the systematic searches (29 September 2026) |
| `99-Meta/protocollo-metanalisi.md` | Current protocol; section 15 is the dated log of every deviation |
| `99-Meta/criteri-screening-meta.md` | Operational screening criteria and exclusion codes (E1–E12) |
| `99-Meta/estrazione-meta.md` | Extraction codebook: outcome codes, thresholds, rules |
| `99-Meta/rob2-meta.md`, `99-Meta/grade-meta.md` | Assessment guides for RoB 2 and GRADE |
| `99-Meta/queries.yaml`, `99-Meta/log/querytranslation-*.txt` | PubMed query (entry `M1-rct-head-to-head`) and its translation by PubMed |
| `99-Meta/ricerca-manuale-meta.md` | Search strings prepared for Embase, CENTRAL and ICTRP, which were not searched |
| `99-Meta/log/ma-ricerca-2026-09-29.md`, `99-Meta/log/fonti-*.json`, `99-Meta/log/citazioni-*.json` | Search log: sources, dates, strings, counts |
| `99-Meta/db/` | Export of the selection database for the meta-analysis records, without abstracts (see below) |
| `99-Meta/log/screening-meta/` | Title/abstract decisions of the two independent agent runs (A, B), in blocks |
| `99-Meta/log/eleggibilita/` | Full-text eligibility evidence sheets |
| `99-Meta/log/estrazione/` | Per-trial extraction: runs A and B, cell-by-cell differences, consensus |
| `99-Meta/log/rob2/`, `99-Meta/log/grade/` | RoB 2 and GRADE: runs A and B, differences, consensus, author decisions |
| `99-Meta/log/fact-check-manoscritto-*.md` | Fact-check log of the manuscript |
| `30-Dati/ma-bracci.csv` | Arm-level data: one row per trial × arm × outcome × window, with source location and verbatim quotation |
| `30-Dati/ma-trial.csv` | Trial characteristics |
| `30-Dati/ma-rob2.csv` | RoB 2 consensus: signalling questions, supporting quotations, domain and overall judgements |
| `50-Metanalisi/` | `analisi.R`, subgroup classification, outputs, GRADE consensus (`grade.csv`), summary of findings (`sof.md`, `grade.md`) |
| `60-Manoscritti/revisione-sistematica/` | Manuscript source and PDF, PRISMA 2020 checklist |
| `.claude/agents/meta-*.md` | Instructions given to the language-model agents (Claude, Anthropic) for each step |
| `CLAUDE.md` | Operating rules of the working repository given to the agents; `analisi.R` also uses it to locate the repository root |

### Selection database export (`99-Meta/db/`)

- `record-meta.csv`: one row per record of the meta-analysis corpus. The `id` column holds a PMID, or for other sources `NCT…`, `EUCTR-…`, `EPMC-…` or `DOI-…`. The file has bibliographic fields, `stato_screening_meta`/`motivo_screening_meta` (title/abstract decision and exclusion code) and `stato_eleggibilita_meta`/`motivo_eleggibilita_meta` (full-text decision and reason).
- `record-query-meta.csv`: which search intercepted each record.
- `trial.csv`, `trial-pubblicazione.csv`: the included trials and the reports and registry records linked to each.

## Glossary

| Italian | English |
|---|---|
| braccio, bracci | arm, arms |
| esito | outcome |
| finestra `primaria` / `estesa` | primary window (day 35 ± 7) / extended window (longest follow-up) |
| soglia | threshold |
| n_randomizzati, n_analizzati | randomised, analysed |
| n_eventi | number of events |
| pagina_o_tabella, citazione | source location, verbatim quotation |
| fonte_dato | data source (fulltext, registry, abstract, supplement) |
| usa_in_analisi | used in the analysis (`si` = yes) |
| consenso | consensus of runs A and B after author adjudication |
| incluso / escluso / dubbio / in-attesa | included / excluded / uncertain / awaiting classification |
| basso / alcune-preoccupazioni / alto | low / some concerns / high (risk of bias) |
| stima, ic_inf, ic_sup | estimate, lower and upper 95% CI |
| rischio_fcm_1000, rischio_fdi_1000 | risk per 1000 with FCM, with FDI |
| sottogruppi | subgroups |
| esclusioni | trials excluded from a model, with reason |

Outcome codes: `P1` hypophosphataemia (< 0.65 mmol/L); `S1` severe hypophosphataemia (≤ 0.32 mmol/L); `S2` hypophosphataemia at the wide threshold (< 0.80 mmol/L); `S3` persistent hypophosphataemia; `S4` serum phosphate as a continuous outcome; `S5` osteomalacia or fractures; `S6` serious or severe hypersensitivity; `S7` any hypersensitivity or infusion reaction; `S8a` adjudicated cardiovascular events; `S8b` serious adverse events in the *Cardiac disorders* and *Vascular disorders* system organ classes.

## Licence

Data, documentation and manuscript: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code (`scripts/`, `50-Metanalisi/analisi.R`): MIT licence, see `LICENSE`. The short verbatim quotations from the included reports are reproduced as supporting evidence for the extraction and the risk-of-bias judgements. Their copyright remains with the original publishers.

## Contact

Filippo Buscemi, UOC Medicina Trasfusionale, ASP di Agrigento: filippo.buscemi@aspag.it
