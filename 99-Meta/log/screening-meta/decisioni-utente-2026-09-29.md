---
tipo: log
descrizione: Decisioni dell'utente sui dubbi dello screening di fase 1 della
  meta-analisi (criteri-screening-meta.md). Il DB ne conserva copia in run_log.
---

# Decisioni dell'utente — fase 1, 2026-09-29

Dubbi prodotti dal doppio screening dei 147 record PubMed (commit `4552268`).

| PMID | Origine del dubbio | Decisione | Motivo registrato |
|---|---|---|---|
| 32479668 | A escluso (E3) / B dubbio | incluso | dati di ipersensibilità da cinque RCT fra cui PHOSPHARE: verificare sul fulltext se riporta dati per braccio FDI vs FCM |
| 35890303 | A dubbio / B dubbio | escluso | E1-non-randomizzato: studio PK in 54 dializzati con iron sucrose, FCM e FDI, randomizzazione non dichiarata |
| 38391240 | A escluso (E3) / B dubbio | escluso | E3-non-primario: modello economico costo-utilità sui dati di PHOSPHARE-IBD, nessun dato originale di trial |
| 41503041 | A dubbio / B dubbio | incluso | database IPD PRAYAS con FCM e iron isomaltoside: verificare sul fulltext se contiene RCT testa a testa |

Esito della fase 1 dopo le decisioni: 19 inclusi, 128 esclusi.

## Secondo giro — altre fonti (commit `5ebc015`)

| Record | Origine del dubbio | Decisione | Motivo registrato |
|---|---|---|---|
| DOI-10.1093_ecco-jcc_jjy222.847 (P723 Detlie) | A dubbio / B dubbio | escluso | E1-non-randomizzato: un ospedale FDI, l'altro FCM; pazienti non randomizzati |
| DOI-10.1007_s40278-017-33473-1 (Reactions Weekly) | A dubbio / B incluso | incluso | solo titolo, verifica sul fulltext |
| EPMC-PMC10576948 (UEG Week 2023) | A escluso / B dubbio | incluso | volume di abstract: regola dei volumi in fase 2 |
| EPMC-PMC10615330 (AMCP 2023) | A escluso / B dubbio | incluso | idem |
| EPMC-PMC11177578 (EHA 2024) | A escluso / B dubbio | incluso | idem |
| EPMC-PMC8548623 (Side Effects of Drugs Annual) | A incluso / B escluso | escluso | E3-non-primario: rassegna annuale |

Regola dei volumi di abstract approvata dall'utente: criteri v1.2.

## Fase 2 — eleggibilità (approvazioni in blocco del 2026-09-29)

Tre tornate di schede (`99-Meta/log/eleggibilita/schede-2026-09-29.md`),
approvate in blocco dall'utente, con le proposte di Claude:

- 1ª e 2ª tornata (43 schede): 4 dubbi risolti come inclusi (38337452, PCR104,
  abstract 337 e LB03 ricavati dai volumi); 33054113 e IJRCOG lasciati in dubbio.
- 3ª tornata: IJRCOG incluso (randomizzazione dichiarata, metodo non descritto:
  RoB 2 dominio 1); preprint di Lubiana incluso; 10 esclusioni; 7 record senza
  sorgente esclusi con E12.
- 33054113 resta `dubbio`: l'approvazione era condizionata alla verifica
  dell'età nella Table 1, non ancora fatta.
- 4ª tornata (ricerca per citazione): protocollo di RAPIDIRON 34556166 e
  abstract EHA P1495 inclusi come secondarie.
- 33054113 incluso: l'utente ha verificato sulla Table 1 che i soggetti sono
  adulti. Diventa il decimo trial (TRIAL-33054113).
