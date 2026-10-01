---
tipo: meta
descrizione: Guida operativa al rischio di bias (RoB 2, Cochrane 2019) per la
  meta-analisi FDI vs FCM (protocollo §10). Definisce il CSV 30-Dati/ma-rob2.csv,
  le domande guida, l'algoritmo e le regole specifiche del vault. La usano
  l'agente meta-rob2 e scripts/rob_meta.py.
versione: "1.2"
---

# RoB 2 — guida operativa

> [!note] Versione 1.2, approvata dall'utente il 2026-09-29.

## 1. Principi

- **Per esito, non per trial** (protocollo §10). Una riga per trial × esito
  usato nell'analisi (`usa_in_analisi = si` in `ma-bracci.csv`).
- **Più risultati usati per lo stesso esito** (es. P1 nelle finestre 0-35 e
  0-70): si valuta il risultato della finestra primaria; per l'altro si scrive
  in `note` il giudizio dei soli domini che cambiano (v1.1).
- **Effetto di interesse: l'assegnazione** (intention-to-treat). Tutti i trial
  confrontano due farmaci attivi; l'aderenza non è l'effetto stimato.
- **Si risponde alle domande guida, poi si applica l'algoritmo.** Il giudizio di
  dominio non si sceglie a sentimento: segue le risposte, salvo scostamento
  motivato per iscritto.
- **Ogni risposta ha una prova** (citazione breve e sede) oppure è `NI` (no
  information). Nessuna conoscenza esterna ai documenti del trial.
- **Fonti ammesse:** tutte le pubblicazioni e registrazioni del trial nel vault
  (`trial_pubblicazione`), più le note di `ma-trial.csv`.

## 2. Risposte e giudizi

Risposte alle domande guida: `Y` (sì), `PY` (probabilmente sì), `PN`
(probabilmente no), `N` (no), `NI` (nessuna informazione), `NA` (non
applicabile, solo dove la guida lo prevede).

Giudizi: `basso` | `alcune-preoccupazioni` | `alto`.

**Convenzione (v1.1):** `Y`/`N` solo quando la fonte lo dichiara direttamente;
`PY`/`PN` quando la risposta è inferita (es. IWRS centralizzato senza
descrizione del metodo di generazione: 1.1 `PY`, 1.2 `Y`).

## 3. Domini e domande guida

### D1 — Processo di randomizzazione
- 1.1 La sequenza di allocazione era casuale?
- 1.2 La sequenza era nascosta fino all'assegnazione?
- 1.3 Le differenze al basale suggeriscono un problema nella randomizzazione?

Algoritmo: `basso` se 1.1 Y/PY/NI, 1.2 Y/PY e 1.3 N/PN/NI; `alto` se 1.2 N/PN,
oppure 1.2 NI e 1.3 Y/PY; altrimenti `alcune-preoccupazioni` (es. 1.2 NI senza
squilibri, o 1.1 N/PN con 1.2 Y/PY).

### D2 — Deviazioni dagli interventi previsti (effetto dell'assegnazione)
- 2.1 I partecipanti erano consapevoli del braccio?
- 2.2 Chi somministrava l'intervento era consapevole?
- 2.3 Se 2.1 o 2.2 Y/PY/NI: ci sono state deviazioni dovute al contesto del trial?
- 2.4 Se 2.3 Y/PY: erano tali da influire sull'esito?
- 2.5 Se 2.4 Y/PY/NI: erano bilanciate fra i bracci?
- 2.6 L'analisi era appropriata per stimare l'effetto dell'assegnazione?
- 2.7 Se 2.6 N/PN/NI: l'errore di analisi poteva avere un impatto sostanziale?

Algoritmo: `basso` se (2.1 e 2.2 N/PN, oppure 2.3 N/PN) e 2.6 Y/PY; `alto` se
2.4 Y/PY e 2.5 N/PN/NI, oppure 2.7 Y/PY; altrimenti `alcune-preoccupazioni`.

### D3 — Dati mancanti dell'esito
- 3.1 I dati dell'esito erano disponibili per tutti o quasi tutti i randomizzati?
- 3.2 Se 3.1 N/PN/NI: ci sono prove che il risultato non sia distorto?
- 3.3 Se 3.2 N/PN: la mancanza poteva dipendere dal valore vero?
- 3.4 Se 3.3 Y/PY/NI: è probabile che ne dipendesse?

Algoritmo: `basso` se 3.1 Y/PY, oppure 3.2 Y/PY, oppure 3.3 N/PN; `alto` se 3.4
Y/PY; altrimenti `alcune-preoccupazioni`.

**Regola del vault:** «quasi tutti» vale come orientamento ≥ 95% per gli esiti
dicotomici rari e ≥ 90% per gli altri; va sempre motivato. Imputazioni
dichiarate (es. persi contati come eventi) si descrivono e si valuta se
cambiano la direzione.

### D4 — Misurazione dell'esito
- 4.1 Il metodo di misurazione era inappropriato?
- 4.2 La misurazione poteva differire fra i bracci?
- 4.3 Chi valutava l'esito era consapevole del braccio?
- 4.4 Se 4.3 Y/PY/NI: la valutazione poteva essere influenzata da questa consapevolezza?
- 4.5 Se 4.4 Y/PY/NI: è probabile che lo sia stata?

Algoritmo: `basso` se 4.1 N/PN/NI, 4.2 N/PN e (4.3 N/PN oppure 4.4 N/PN); `alto`
se 4.1 Y/PY, oppure 4.2 Y/PY, oppure 4.5 Y/PY/NI; altrimenti
`alcune-preoccupazioni`.

**Regola del vault (protocollo §10):** gli esiti di laboratorio (P1, S1, S2,
S3, S4) sono misure oggettive: 4.4 di norma `N` anche in un trial open-label.
Gli esiti di sicurezza giudicati dal clinico (S6, S7, S8b) in un trial
open-label o con valutatore non mascherato: 4.4 di norma `PY`, salvo
aggiudicazione in cieco documentata.

### D5 — Selezione del risultato riportato
- 5.1 I dati sono stati analizzati secondo un piano prespecificato, finalizzato
  prima dello sblocco dei dati?
- 5.2 Il risultato è stato scelto fra più misure dell'esito (scale, definizioni,
  tempi) in base ai risultati?
- 5.3 Il risultato è stato scelto fra più analisi in base ai risultati?

Algoritmo: `basso` se 5.1 Y/PY e 5.2 e 5.3 N/PN; `alto` se 5.2 o 5.3 Y/PY;
altrimenti `alcune-preoccupazioni` (5.1 N/PN/NI, oppure 5.2/5.3 NI).

**Regola del vault:** si confrontano registro, protocollo pubblicato e
articoli. Un esito del codebook **prespecificato ma non riportato**, o
riportato come esito primario mentre il registro ne indicava un altro, va
discusso esplicitamente in 5.1-5.2 (le note di `ma-trial.csv` li elencano).
Un esito post hoc (es. S1 nei registri PHOSPHARE-IDA) ha 5.1 `N`.

### Giudizio complessivo
- `basso` se tutti i domini sono `basso`;
- `alcune-preoccupazioni` se almeno un dominio lo è e nessuno è `alto`;
- `alto` se almeno un dominio è `alto`, **oppure** se più domini hanno
  `alcune-preoccupazioni` in modo da ridurre sostanzialmente la fiducia
  (motivarlo in `note`).

**Regola del vault (v1.2):** il complessivo si porta ad `alto` quando quattro o
più domini hanno `alcune-preoccupazioni` **e** la pubblicazione ha incoerenze
interne documentate (denominatori, tabelle o disegno contraddittori). Tre
domini `alcune-preoccupazioni` che dipendono dallo stesso problema (es. gli
stessi pazienti esclusi in D2 e mancanti in D3) non bastano da soli.

## 4. `30-Dati/ma-rob2.csv`

Una riga per trial × esito.

| Colonna | Contenuto |
|---|---|
| `trial_id`, `esito` | come in `ma-bracci.csv` |
| `effetto` | `assegnazione` |
| `d1_sq` … `d5_sq` | risposte alle domande guida, es. `1.1 Y; 1.2 NI; 1.3 N` |
| `d1` … `d5` | giudizio del dominio |
| `d1_supporto` … `d5_supporto` | prove: citazioni brevi con sede e pmid, separate da ` ‖ ` |
| `complessivo` | giudizio complessivo |
| `valutatore` | `A` \| `B` \| `consenso` |
| `note` | scostamenti dall'algoritmo (cominciano con `scostamento:`), motivazioni, rimandi |

## 5. Procedura

1. Due valutazioni indipendenti per trial (agente `meta-rob2`, passaggi A e
   B), tutte le combinazioni di quel trial in un file.
2. `scripts/rob_meta.py --confronta` segnala giudizi e risposte diversi.
3. L'utente decide le discordanze; il consenso va in `30-Dati/ma-rob2.csv`.

## Registro delle versioni

| Versione | Data | Nota |
|---|---|---|
| 1.0 | 2026-09-29 | Prima stesura, dal protocollo §10 e dalle segnalazioni raccolte in estrazione; approvata dall'utente |
| 1.1 | 2026-09-29 | Dal pilota PHOSPHARE-IBD: convenzione Y/N vs PY/PN; più risultati per esito; approvata dall'utente |
| 1.2 | 2026-09-29 | Da IJRCOG e i3R: regola del complessivo alto per cumulo; approvata dall'utente |
