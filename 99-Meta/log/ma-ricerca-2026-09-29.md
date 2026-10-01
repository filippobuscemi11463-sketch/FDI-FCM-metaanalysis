---
tipo: log
descrizione: Registro della ricerca bibliografica della meta-analisi FDI vs FCM
  (protocollo v1.0, §7). Una riga per fonte, con data, numeri e sede della stringa.
---

# Ricerca per la meta-analisi — 2026-09-29

Protocollo: `99-Meta/protocollo-metanalisi.md` v1.0 (commit `fc19a3a`).

## Fonti interrogate

| Fonte | Data | Stringa / filtri | Record identificati | Importati | Note |
|---|---|---|---|---|---|
| PubMed/MEDLINE | 2026-09-29 16:55 | `M1-rct-head-to-head` — term e querytranslation in `querytranslation-M1-rct-head-to-head-2026-09-29.txt` | 148 | 147 | nessun limite di data (controllo §7.1 superato); 1 PubmedBookArticle non importato: 42118883 (CADTH Health Technology Review, «Ferric Derisomaltose for Heart Failure and Iron Deficiency», 2026) |
| Cochrane CENTRAL | — | stringa in `99-Meta/ricerca-manuale-meta.md` | — | — | da eseguire dall'utente |
| ClinicalTrials.gov | 2026-09-29 | API v2, `query.term` — stringa esatta in `fonti-meta-2026-09-29.json` | 13 | 13 | nessun limite di data; verificata la coerenza: l'intersezione delle ricerche FDI e FCM separate dà gli stessi 13 NCT |
| EU CTR | 2026-09-29 | ricerca pubblica, stringa in `fonti-meta-2026-09-29.json` | 4 | 4 | |
| EU CTIS | 2026-09-29 | API pubblica, un prodotto per volta, intersezione FDI ∩ FCM | 0 | 0 | lato FDI 7 trial, lato FCM 10: nessuno in comune |
| WHO ICTRP | — | stringa in `99-Meta/ricerca-manuale-meta.md` | — | — | da eseguire dall'utente (nessun accesso automatico) |
| Europe PMC | 2026-09-29 | REST, `NOT SRC:MED`, campi di default (fulltext OA compreso) | 38 | 38 | 8 preprint, 30 articoli PMC non indicizzati in MEDLINE |
| Embase | — | stringa in `99-Meta/ricerca-manuale-meta.md` | — | — | da eseguire dall'utente in Firefox |
| Consensus (supplementare) | 2026-09-29 | 3 query, in `fonti-meta-consensus-2026-09-29.json` | 30 | 4 | importati solo i record assenti dal DB, tutti abstract congressuali, DOI verificati su Crossref |
| Crossref (deviazione §15) | 2026-09-29 | 24 coppie FDI×FCM in `query.bibliographic`, stop a 200 consecutivi senza corrispondenze (tetto 2000), filtro titolo+abstract; dettaglio per coppia in `fonti-meta-2026-09-29.json` | 92 | 40 | 51 già presenti per DOI; 1 duplicato per titolo fuso a mano (A216, J Can Assoc Gastroenterol 2025: stesso abstract già da Europe PMC, `EPMC-PMC11807454`). Soprattutto abstract congressuali (ERA/NDT, WCN, ECCO, ASH, ISPOR) |
| Altri metodi | 2026-09-29 | trovato durante la verifica Crossref, non da ricerca sistematica | 1 | 1 | 10.1182/blood-2022-165923 |
| Ricerca per citazione | 2026-09-29 | Europe PMC: riferimenti di 37 semi (15 pubblicazioni incluse + 17 revisioni/meta-analisi del corpus + fonti-di-riferimenti) e citazioni in avanti delle 15 incluse; filtro allargato (vedi sotto); dettaglio in `citazioni-meta-2026-09-29.json` | 1124 identificativi, 951 non nel DB | 190 | 188 PubMed + 1 preprint + abstract EHA 2023 P1495 (dal rif. 11 del PDF IJRCOG) |

## PubMed — composizione dei 147 record importati

| Corpus | Record | Significato |
|---|---|---|
| `meta` | 97 | nuovi, fuori dal wiki; 54 pubblicati prima del 2021 |
| `wiki+meta` | 50 | già nel wiki (29 inclusi, 21 esclusi dal suo screening) |

Anni di pubblicazione: 2011–2026. Record con publication type *Randomized
Controlled Trial*: 13 (conteggio indicativo; lo screening non usa il publication
type come criterio).

Screening di fase 1 dei 147 record PubMed completato il 2026-09-29: 19 inclusi,
128 esclusi (dettaglio in `screening-meta/`). I 100 record delle altre fonti sono
ancora da valutare.

## Osservazione del 2026-09-29: gli abstract congressuali

Consensus ha trovato 4 abstract congressuali (supplementi di J Crohn's Colitis,
Blood, J Endocr Soc) che né PubMed né Europe PMC restituiscono. È il segnale di
un buco sistematico: gli atti dei congressi (ASH, ECCO, ENDO, ASN, ESC…) sono
in gran parte fuori da MEDLINE. Embase li indicizza, quindi la ricerca Embase va
fatta **senza** escludere i conference abstract.

## Osservazione del 2026-09-29: trial testa a testa descritti senza nominare i farmaci

Il protocollo di RAPIDIRON (PMID 34556166, Trials 2021) confronta FCM e FDI ma
nel titolo e nell'abstract parla solo di «two different intravenous
formulations». M1 non poteva trovarlo, e nemmeno il filtro a due termini della
ricerca per citazione. Per questo la ricerca per citazione usa un filtro
allargato: entrambi i farmaci, **oppure** un farmaco o il ferro EV in un record
randomizzato. È un limite di sensibilità delle stringhe su titolo/abstract da
dichiarare nel lavoro; Embase (indicizzazione per farmaco, Emtree) lo attenua.
