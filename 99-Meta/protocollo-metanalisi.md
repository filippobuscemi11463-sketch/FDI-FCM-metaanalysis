---
tipo: meta
descrizione: Protocollo pre-specificato della revisione sistematica con
  meta-analisi degli RCT testa a testa FDI vs FCM. Governa lo strato
  50-Metanalisi/. Nessun calcolo aggregato si esegue prima del suo commit.
versione: 1.0
stato: congelato — ogni modifica successiva è una deviazione (§15)
---

# Protocollo — revisione sistematica e meta-analisi FDI vs FCM

> [!important] Versione 1.0, congelata il 2026-09-29. Hash e data del commit
> di congelamento sono la prova di anteriorità rispetto all'estrazione per
> braccio e a ogni calcolo aggregato. Ogni modifica successiva è una deviazione
> e va registrata in §15.

## 1. Titolo di lavoro

*Ferric derisomaltose versus ferric carboxymaltose: systematic review and
meta-analysis of head-to-head randomised controlled trials on hypophosphataemia,
osteomalacia, hypersensitivity and cardiovascular events.*

## 2. Registrazione

- Registro: **OSF Registries**. PROSPERO va verificato ma è probabile il
  rifiuto, perché l'estrazione di parte dei dati (non per braccio) esiste già
  nel vault.
- La registrazione dichiara in modo esplicito che: (a) il vault conteneva già
  note ed estrazioni non strutturate per braccio dei trial candidati; (b) il
  protocollo è stato scritto dopo, ma prima dell'estrazione per braccio e di
  ogni calcolo aggregato; (c) l'hash del commit di congelamento.

## 3. Razionale

L'ipofosfatemia è il principale discriminante noto fra le due molecole. Le
meta-analisi esistenti usano in larga parte gli stessi trial. Il contributo
atteso non è una stima nuova ma una stima **tracciabile e aggiornabile**: ogni
numero aggregato risale per script alla riga di dato e alla tabella del trial.

## 4. Domanda (PICOS)

| | Criterio |
|---|---|
| **P** | Persone con carenza marziale, con o senza anemia, di qualsiasi eziologia. **Solo adulti** (≥ 18 anni). Trial misti adulti/minori: inclusi solo se i dati degli adulti sono separabili, oppure se i minori sono < 10% dei randomizzati (dichiarato) |
| **I** | FDI (ferric derisomaltose / iron isomaltoside 1000), qualsiasi dose e schema EV |
| **C** | FCM (ferric carboxymaltose), qualsiasi dose e schema EV |
| **O** | §6 |
| **S** | RCT con randomizzazione diretta fra un braccio FDI e un braccio FCM. Ammessi i trial a più bracci: si usano solo i bracci FDI e FCM |

### Esclusioni

- Studi non randomizzati, quasi-randomizzati (alternanza, data di nascita),
  confronti indiretti, estensioni open-label senza randomizzazione.
- Trial in cui FDI o FCM sono co-somministrati con un altro ferro EV nello
  stesso braccio.
- Crossover: **inclusi usando solo il primo periodo**, che equivale a un
  confronto parallelo randomizzato fra pazienti non esposti. Il secondo periodo
  non si usa mai: il ferro EV lascia depositi pieni per mesi, l'ipofosfatemia
  da FCM può durare settimane e una prima esposizione può sensibilizzare, quindi
  il washout non ripristina la condizione di partenza. Se il primo periodo non
  è pubblicato separatamente, il trial si elenca e non si aggrega, con il
  motivo scritto. Deciso il 2026-09-29.
- Nessun limite di data (vedi §7.1), lingua o stato di pubblicazione: sono ammessi abstract
  congressuali e risultati depositati nei registri, se riportano dati per braccio.

## 5. Unità di analisi: il trial, non il PMID

Più pubblicazioni dello stesso trial (primaria, post-hoc, analisi secondarie)
si raggruppano sotto un **identificativo di trial**: il numero di registro
(NCT, EudraCT, ISRCTN) oppure, se assente, `TRIAL-<pmid-primaria>`.

- Per ogni esito, il dato viene dalla pubblicazione che lo riporta sulla
  popolazione più completa. A parità, la primaria.
- Un trial contribuisce **una sola volta** a ciascuna analisi.
- I trial gemelli pubblicati insieme (es. due trial nello stesso articolo) sono
  due unità, se randomizzati separatamente.

## 6. Esiti

Tutti dicotomici, per paziente (non per evento), salvo dove indicato.

### 6.1 Esito primario

**Incidenza di ipofosfatemia** definita come fosfato sierico
**< 0,65 mmol/L (< 2,0 mg/dL)** in qualsiasi misurazione entro la finestra
primaria (§6.5).

Motivo della soglia: è la soglia più usata nel vault (46 righe su 136 con
soglia valorizzata, 239 righe totali, in `30-Dati/ipofosfatemia.csv` al 2026-09-29) e coincide
con l'endpoint primario dei trial PHOSPHARE-IDA A e B: «incidence of
hypophosphatemia (serum phosphate level <2.0 mg/dL) between baseline and day
35» — PMID 32016310, doi:10.1001/jama.2019.22450, *Main Outcomes and Measures*
(abstract strutturato; il body del fulltext PMC non era restituibile il
2026-09-29). 2,0 mg/dL × 0,3229 = 0,646 mmol/L. Soglia confermata il
2026-09-29. La definizione nei Methods si ricontrolla sul fulltext durante
l'estrazione per braccio.

### 6.2 Esiti secondari

| Codice | Esito | Definizione |
|---|---|---|
| S1 | Ipofosfatemia grave | fosfato ≤ 0,32 mmol/L (≤ 1,0 mg/dL) |
| S2 | Ipofosfatemia a soglia larga | fosfato < 0,80 mmol/L (< 2,5 mg/dL); raggruppa anche 0,81 mmol/L |
| S3 | Ipofosfatemia persistente | fosfato < 0,65 mmol/L all'ultima visita della finestra primaria |
| S4 | Variazione del fosfato | differenza media del nadir o della variazione dal basale (continuo, MD) |
| S5 | Osteomalacia e fratture | osteomalacia diagnosticata, oppure fratture da fragilità / pseudofratture, come riportate |
| S6 | Ipersensibilità grave | anafilassi o reazione di ipersensibilità grave/seria: criteri NIAID/FAAN o WAO se il trial li usa; altrimenti Ring & Messmer ≥ II, oppure evento serio (SAE) con termine MedDRA della SMQ *Anaphylactic reaction* |
| S7 | Ipersensibilità, qualsiasi | qualsiasi evento classificato dal trial come ipersensibilità o reazione infusionale, SMQ *Hypersensitivity* ampia |
| S8 | Eventi cardiovascolari | principale: eventi aggiudicati come definiti dal trial; sensibilità: SAE delle SOC MedDRA *Cardiac disorders* + *Vascular disorders* |

**S8 — opzioni per gli eventi cardiovascolari:**

- (a) *adjudicated* cardiovascular events come definiti dal trial (MACE o
  composito), se esistono;
- (b) eventi avversi seri della SOC MedDRA *Cardiac disorders* + *Vascular
  disorders*;
- (c) entrambi, con (a) come principale e (b) come sensibilità.

Scelta: (c), decisa il 2026-09-29. L'ipertensione o l'aumento pressorio post-infusione si registra
dentro (b), non come esito separato.

### 6.3 Esiti attesi come non stimabili

S5 (osteomalacia) è con alta probabilità assente o a zero eventi negli RCT
testa a testa. **Si dichiara ora** che, se meno di 2 trial riportano almeno un
evento, S5 non si aggrega e si descrive in forma narrativa, con il numero di
trial che lo hanno cercato e il follow-up. La stessa regola vale per S6.

### 6.4 Esiti riportati diversamente

- Soglia diversa da quelle pre-specificate: il trial entra solo nell'esito con
  la soglia più vicina **per difetto**, e la differenza viene dichiarata e
  testata in sensibilità (§11, analisi 3). Deciso il 2026-09-29.
- Solo la percentuale senza denominatore: si ricostruisce n dal denominatore
  randomizzato **solo** se la fonte lo consente senza ambiguità; altrimenti il
  trial è escluso dall'analisi di quell'esito, e il motivo si registra.

### 6.5 Finestre temporali

- **Finestra primaria:** dalla prima dose a 35 giorni (± 7) dopo la prima
  dose, oppure il timepoint primario del trial se compreso fra 28 e 42 giorni.
- **Finestra estesa:** il follow-up più lungo disponibile, analizzato
  separatamente. Non si fondono finestre diverse nella stessa stima.

## 7. Fonti e ricerca

| Fonte | Accesso | Note |
|---|---|---|
| PubMed/MEDLINE | E-utilities | query dedicata `M1-rct-head-to-head` **senza finestra temporale** |
| Cochrane CENTRAL | Cochrane Library, ricerca manuale documentata | include record da Embase e da registri |
| ClinicalTrials.gov | API v2 | trial completati, anche senza pubblicazione |
| EU CTR / CTIS | ricerca web documentata | |
| WHO ICTRP | ricerca web documentata | |
| Europe PMC | REST | preprint e abstract congressuali |
| Embase | accesso istituzionale dell'utente, via Firefox | ricerca eseguita dall'utente con la stringa del protocollo; export RIS/CSV importato da script. Nessuna interrogazione automatica |
| Consensus | MCP / web, query registrate con data | **solo fonte supplementare** («altri metodi» nel diagramma PRISMA): non è riproducibile né esaustiva. Ogni record deve risalire a PMID o DOI verificato. Un trial trovato solo qui segnala un buco nelle query |
| Ricerca per citazione | manuale | riferimenti dei trial inclusi e delle revisioni in `fonti-di-riferimenti.md`, più citazioni in avanti |

Stringa PubMed (`M1-rct-head-to-head`): blocchi `{FDI} AND {FCM}` di `queries.yaml`, senza
finestra e **senza filtro di disegno** in fase di ricerca. Lo screening
seleziona gli RCT; un filtro di disegno a monte perderebbe gli RCT mal
indicizzati. Nessuna esclusione di publication type, eccetto errata.

### 7.1 Limiti temporali — nessun limite anteriore

- **Ogni fonte si interroga dalla sua data di inizio (inception) alla data di
  esecuzione.** Nessun limite anteriore di data, in nessuna fonte, né in fase
  di ricerca né in fase di screening. L'anno di pubblicazione non è mai un
  motivo di esclusione.
- La finestra mobile di 5 anni di `queries.yaml` (`finestra.anni_indietro`)
  **non si applica** al corpus `meta`.
- **Attuazione tecnica (2026-09-29).** `M1-rct-head-to-head` sta nella sezione
  `query_meta` di `queries.yaml` con `finestra: nessuna`. `build_term()` non
  aggiunge limiti di data alle query così marcate e rifiuta un term che ne
  contenga uno. `--all` non esegue le query di `query_meta`, e
  `pubmed_harvest.py` le accetta solo con `--dry-run` finché `state.sqlite` non
  distingue i corpora (§8). Le query Q1–Q9 del wiki producono term identici a
  prima della modifica.
- **Controllo bloccante:** la `querytranslation` restituita da PubMed per `M1`
  si salva nel log della ricerca e **non deve contenere alcun limite di data**
  (`[dp]`, `[pdat]`, `[edat]`, `mindate`, `reldate`). Se ne contiene uno, la
  ricerca è invalida e si ripete. Il controllo è automatico in
  `pubmed_harvest.py`, che salva term e querytranslation in
  `99-Meta/log/querytranslation-<query>-<data>.txt`; la prova a vuoto del
  2026-09-29 (148 record) è passata. Lo stesso vale per le stringhe e i filtri
  usati nelle altre fonti, che si registrano con uno screenshot o un export.
- Conteggio di controllo del 2026-09-29, blocchi `{FDI} AND {FCM}` su PubMed:
  148 record senza limiti di data, 80 con la finestra di 5 anni. Con il filtro
  `randomized controlled trial[pt]`, solo per controllo e non per la ricerca:
  13 senza limiti, di cui 2 pubblicati prima del 2021-09-29.

La data di esecuzione e il numero di record per fonte si registrano in
`99-Meta/log/ma-ricerca-<data>.md`.

## 8. Selezione

1. Deduplicazione per PMID, DOI e numero di registro.
2. Screening di titolo e abstract con `triage-screener`, usando criteri propri
   di questo protocollo (§4), distinti da `criteri-screening.md`.
3. Eleggibilità sul fulltext: decisione dell'utente su ogni record.
4. Diagramma di flusso PRISMA 2020 generato da `state.sqlite`.

**Separazione dei corpora.** I record entrano in `state.sqlite` con
`corpus = 'meta'`. Un record già presente nel wiki riceve anche l'etichetta
`meta` senza perdere quella `wiki`. Lint, conteggi e sintesi del wiki ignorano i
record solo-`meta`.

## 9. Estrazione dei dati

CSV nuovo e separato, `30-Dati/ma-bracci.csv`. I CSV esistenti non si toccano.

Intestazione (si possono aggiungere colonne di servizio; togliere o ridefinire quelle elencate è una deviazione):

```
trial_id,pmid,braccio,farmaco,dose_totale_mg,schema,n_randomizzati,n_analizzati,
popolazione_analisi,esito,finestra,soglia_mmol_l,n_eventi,media,ds,
tempo_misura_giorni,pagina_o_tabella,fonte_dato,estrattore,note
```

- Una riga per trial × braccio × esito × finestra.
- **Doppia estrazione indipendente:** due agenti estraggono separatamente, senza
  vedere l'uno l'output dell'altro. Uno script confronta le due estrazioni
  cella per cella. Ogni discordanza la decide l'utente.
- **Verifica umana al 100%:** l'utente controlla sul PDF ogni riga che entra in
  un'analisi aggregata. Con pochi trial è fattibile, e rende il metodo
  difendibile.
- Popolazione di analisi preferita: randomizzati che hanno ricevuto almeno una
  dose (safety set). In alternativa si usa quella del trial e la si dichiara.
- Dati da registri o supplementi: `fonte_dato = registro | supplementare`.

Si estraggono anche, per trial: registro, sponsor, finanziamento, paese,
popolazione, criteri di fosfato al basale, dosi, cecità, follow-up, conflitti.

## 10. Rischio di bias

- **RoB 2** (Cochrane), per esito e non per trial. Motivo: in un trial open-label
  il fosfato, misurato in laboratorio, è a basso rischio di bias di
  misurazione, mentre l'ipersensibilità, giudicata dal clinico, non lo è.
- Doppia valutazione indipendente (due agenti), con riconciliazione dell'utente.
- Output in `30-Dati/ma-rob2.csv`, un dominio per colonna, con le frasi di
  supporto citate con la loro sede.

## 11. Sintesi statistica

Tutti i numeri aggregati li produce **uno script**, mai l'LLM. Lo script legge
solo `ma-bracci.csv` e scrive gli output in `50-Metanalisi/output/`, con il
checksum dell'input.

| Elemento | Scelta |
|---|---|
| Software | R, pacchetto `metafor` (versione fissata in `renv.lock`; vedi §15: versioni registrate in `50-Metanalisi/output/run.txt`) |
| Misura d'effetto, dicotomici | Risk ratio (RR) con IC 95%; anche la differenza di rischio (RD) per S5–S8 |
| Misura d'effetto, continui | Differenza media (MD) |
| Modello principale | Effetti casuali, stimatore di τ² REML, IC con correzione Hartung-Knapp-Sidik-Jonkman |
| Con k < 5 trial | Si riporta comunque, affiancato a Mantel-Haenszel a effetti fissi: con pochi trial l'HKSJ produce intervalli molto ampi, e i lettori devono vedere entrambi |
| Eterogeneità | τ², I², Q; intervallo di predizione se k ≥ 3 |
| Aggregazione minima | k ≥ 2 trial con dati per l'esito; sotto questa soglia, sintesi narrativa |
| Eventi rari (S5–S8) | Principale: RR di Mantel-Haenszel senza correzione di continuità; i trial a doppio zero sono esclusi dal RR ma inclusi nella RD. Sensibilità: Peto OR; modello beta-binomiale o GLMM se k ≥ 3 |
| Correzione di continuità | Nessuna nel modello principale; 0,5 solo in sensibilità |

### Analisi di sensibilità (pre-specificate)

1. Solo trial a basso rischio di bias complessivo (RoB 2) per quell'esito.
2. Effetti fissi vs effetti casuali.
3. Esclusione dei trial con soglia di fosfato non esattamente coincidente (§6.4).
4. Esclusione dei trial finanziati dal produttore di una delle due molecole.
   **Atteso vuoto:** se lo è, lo si scrive, non lo si omette.
5. Esclusione dei dati provenienti solo da registro o abstract.

### Sottogruppi (esplorativi, solo con k ≥ 2 per sottogruppo)

- Popolazione: IBD; IDA generica; ostetricia (gravidanza, post-partum);
  scompenso cardiaco; nefropatia.
- Schema di dose: singola dose FDI vs frazionata FCM, rispetto a dosi
  cumulative equivalenti.

Nessuna inferenza dai sottogruppi viene presentata come confermativa.

### Bias di pubblicazione

Funnel plot e test di Egger **solo se k ≥ 10** (non atteso). In alternativa:
confronto fra trial registrati come completati e trial pubblicati, da
ClinicalTrials.gov e ICTRP.

## 12. Certezza dell'evidenza

**GRADE** per ogni esito, con la tabella Summary of Findings. I giudizi
(rischio di bias, incoerenza, indirettezza, imprecisione, bias di
pubblicazione) sono motivati per iscritto in `50-Metanalisi/grade.md`.

## 13. Tracciabilità (specifica di questo vault)

- Ogni stima in `50-Metanalisi/` cita: commit dello script, checksum di
  `ma-bracci.csv`, righe di input (trial_id + pagina_o_tabella).
- `vault-lint` si estende con un controllo: ogni numero in `50-Metanalisi/`
  deve coincidere con un output dello script.
- Le note di `40-Sintesi/` possono citare le stime aggregate solo linkando
  `50-Metanalisi/`, mai trascrivendole senza link.

## 14. Rapporto con il wiki

- La regola di CLAUDE.md §9 («il vault non fa meta-analisi») diventa: *nessuna
  sintesi quantitativa fuori da questo protocollo e fuori da `50-Metanalisi/`*.
- La finestra mobile di 5 anni resta la regola del wiki. La query senza
  finestra vale solo per il corpus `meta`.
- La modifica di CLAUDE.md si fa **dopo** il congelamento del protocollo.

## 15. Deviazioni dal protocollo

| Data | Sezione | Deviazione | Motivo | Decisa da |
|---|---|---|---|---|
| 2026-09-29 | §8.2 | Screening di titolo e abstract **doppio e indipendente** (due passaggi di agente, discordanze all'utente) invece che singolo | standard delle revisioni sistematiche; permette di riportare l'accordo fra screener. Aggiunta prima di qualsiasi screening del corpus `meta` | utente |
| 2026-09-29 | §8.3, §11 | I protocolli e le registrazioni di RCT testa a testa senza risultati ricevono lo stato `in-attesa` («in attesa di classificazione», PRISMA 2020) invece di essere esclusi | servono al confronto trial registrati vs pubblicati del §11. Deciso prima di qualsiasi screening | utente |
| 2026-09-29 | §8 | Criteri operativi in `99-Meta/criteri-screening-meta.md` v1.0 | rendono operativo il §4 senza modificarlo | utente |
| 2026-09-29 | §6.2, §11 | **S4, tempo di analisi**: analisi principale sulla variazione del fosfato dal basale al giorno 35 (fine della finestra primaria, stesso tempo per tutti i trial); il nadir, il cui giorno varia fra farmaci e trial, come analisi di sensibilità | il §6.2 ammette «nadir o variazione dal basale» senza fissare il tempo; scelto prima di qualsiasi calcolo | utente |
| 2026-09-29 | §9 | Codebook dell'estrazione in `99-Meta/estrazione-meta.md` e secondo CSV `30-Dati/ma-trial.csv` (caratteristiche dei trial); a `ma-bracci.csv` si aggiungono colonne di servizio (`soglia_testo`, `percentuale`, `tipo_dispersione`, `misura_continua`, `unita`, `citazione`, `usa_in_analisi`) senza togliere o ridefinire quelle del §9 | rendono l'estrazione verificabile riga per riga | utente (codebook approvato il 2026-09-29) |
| 2026-09-29 | §7 | Ricerca per citazione su Europe PMC (riferimenti all'indietro di inclusi e revisioni, citazioni in avanti degli inclusi) con **filtro allargato**: entrambi i farmaci, oppure un farmaco o il ferro EV in un record randomizzato | il protocollo di RAPIDIRON non nomina FDI né FCM in titolo e abstract e sfuggiva al filtro a due termini | utente (via libera alla ricerca per citazione) |
| 2026-09-29 | §7 | **Crossref aggiunto come fonte sistematica** per gli abstract congressuali pubblicati nei supplementi delle riviste. Regola: 24 coppie di sinonimi FDI×FCM in `query.bibliographic`, scorrimento per pertinenza fino a 200 risultati consecutivi senza corrispondenze (tetto 2000), filtro locale su titolo+abstract (≥1 termine FDI e ≥1 FCM) | Consensus ha trovato 4 abstract congressuali assenti da PubMed ed Europe PMC: buco sistematico delle fonti gratuite. Limite dichiarato: l'ordinamento per pertinenza di Crossref non è garantito stabile nel tempo | utente |
| 2026-09-29 | §11 | **Modello principale con celle zero**: per P1–S3, se le celle zero escluderebbero trial dal REML senza correzione, il modello principale è Mantel-Haenszel; se un braccio non ha eventi in nessun trial (RR non definito), le misure principali sono Peto OR e RD di Mantel-Haenszel. REML + HKSJ resta affiancato, la correzione 0,5 resta in sensibilità | alla prima run S1 (0 eventi con FDI in tutti i trial) non era stimabile, e per S3 il REML perdeva PHOSPHARE-IDA05; regola decisa dopo aver visto quali modelli erano stimabili, prima di qualsiasi GRADE | utente |
| 2026-09-29 | §6.2, §11 | **S7 in sintesi narrativa**, senza stima aggregata: i due trial usano definizioni diverse (reazione di Fishbane e orticaria vs «infusion-related reaction probably/highly probably related») e hanno effetti di direzione opposta; le stime per trial sono in `50-Metanalisi/output/trial-singoli.csv` | eterogeneità clinica; con k = 2 il modello a effetti casuali non è informativo e quello fisso coincide di fatto con un solo trial. Decisione presa dopo aver visto i dati: da dichiarare come tale | utente |
| 2026-09-29 | §11 | **Versioni dei pacchetti**: `metafor` e `lme4` installati da CRAN nella libreria R utente; le versioni esatte sono registrate a ogni run in `50-Metanalisi/output/run.txt` (`sessionInfo()`), al posto di `renv.lock` | installazione senza privilegi di amministratore; la tracciabilità delle versioni è conservata | utente |
| 2026-09-29 | §10, §12 | Guide operative `99-Meta/rob2-meta.md` e `99-Meta/grade-meta.md`, approvate prima di ciascuna valutazione. GRADE: approccio minimamente contestualizzato con soglia nulla, dimensione informativa ottimale ~300 eventi o ~400 partecipanti, bias di pubblicazione provvisorio finché mancano Embase/CENTRAL/ICTRP, doppia valutazione indipendente (il §12 non la specificava) | rendono operativi §10 e §12 senza modificarli | utente |
| 2026-09-29 | §11 | **Regola di aggregazione riallineata al protocollo** dopo la verifica del manoscritto: lo script non aggregava nessun esito con meno di 2 trial con eventi, mentre il §11 chiede 2 trial con dati e il §6.3 limita la condizione sugli eventi a S5 e S6. Ora: RD di Mantel-Haenszel (doppi zeri inclusi) come misura principale quando meno di 2 trial hanno eventi; nessuna stima se nessun trial ha eventi (RD degenere). Effetto: S8b estesa aggregata come RD | correzione di un errore dello script, dopo aver visto i dati | utente |
| 2026-09-29 | §11 | **Sottogruppi esplorativi eseguiti** con la classificazione di `50-Metanalisi/sottogruppi.csv` (schema di dose e popolazione, dai campi di `ma-trial.csv`); stima per livello con il modello principale e Q fra gruppi. Il sottogruppo per popolazione non è eseguibile (un solo livello con almeno 2 trial) | analisi prespecificata ma omessa nella prima run; classificazione scritta dopo aver visto i dati | utente |
| 2026-09-29 | §6.2, §15 | **Nadir del fosfato (sensibilità di S4) non eseguito**: il nadir non è stato estratto dal codebook | dichiarato come analisi prespecificata non eseguita | utente |
| 2026-09-29 | §11 | **Confronto fra trial registrati e pubblicati** fatto in forma descrittiva dai record di registro del database (nessun funnel plot, k < 10) | rende operativo il §11 | utente |
| 2026-09-29 | §7 | Ricerca per citazione **automatizzata** su Europe PMC (riferimenti e citazioni via API) invece che manuale | riproducibile; dettaglio in `citazioni-meta-2026-09-29.json` | utente |
| 2026-09-29 | §9, §10 | Codebook dell'estrazione (v1.1, v1.2) e guida RoB 2 (v1.1, v1.2) **aggiornati durante i piloti**: regole nate dall'estrazione di PHOSPHARE-IBD e IDA04/05 e dalla valutazione di IJRCOG e i3R (complessivo alto per cumulo di domini). Ogni versione approvata dall'utente; la regola del complessivo alto per cumulo (RoB 2 v1.2) è stata scritta risolvendo la discordanza su IJRCOG e applicata allo stesso trial, e la regola 9 del codebook (zeri dagli elenchi di SAE) è stata ricavata da IDA04/05 e applicata agli stessi trial | le regole sono nate dall'esperienza sui dati | utente |
| 2026-09-29 | §6.4 | **ExplorIRON-CKD tolto da S1**: soglia 0,30 mmol/L, sotto la soglia S1 (0,32) e senza soglia di protocollo inferiore, quindi per la regola «soglia più vicina per difetto» non entra in S1. Riga RoB 2 corrispondente rimossa da `ma-rob2.csv` (resta nel log) | applicazione del protocollo, segnalata dalla verifica del manoscritto dopo aver visto i dati | utente |
| 2026-09-29 | §11 | La **RD come misura principale** quando meno di 2 trial hanno eventi è una regola nuova, non prevista dal §11 (che prevede la RD accanto al RR per S5–S8) | vedi riga «regola di aggregazione» | utente |
| 2026-09-29 | §7, §11 | **Embase, CENTRAL e ICTRP non ancora interrogati**; il confronto fra trial registrati e pubblicati usa solo i record di registro nel database (ClinicalTrials.gov, EU CTR), non ICTRP, e non si limita ai trial registrati come completati | limite dichiarato | utente |
| 2026-09-29 | §8 | Criteri di screening rivisti due volte (v1.1 dopo lo screening dei 147 PubMed, v1.2 regola dei volumi in fase 2); schede di eleggibilità preparate da **un solo** passaggio di agente, decisioni dell'utente approvate in blocco sulle proposte | trasparenza sul processo | utente |
| 2026-09-29 | §11 | Sottogruppo di dose definito come «FDI singola vs FCM frazionata» contro «stesso schema nei due bracci», non «rispetto a dosi cumulative equivalenti»; livello «volontari sani» aggiunto; lo script legge anche `50-Metanalisi/sottogruppi.csv` oltre a `ma-bracci.csv` | classificazione fattibile con i dati estratti | utente |
| 2026-09-29 | §6.5 | **ExplorIRON-CKD usato anche per P1 nella finestra estesa** (0-60 giorni, zero in entrambi i bracci), lo stesso zero sull'intero studio già usato per la finestra primaria; la riga era rimasta non usata senza motivo scritto. P1 estesa passa da 1 a 2 trial (1 con eventi): RD come misura principale | segnalato dalla terza verifica del manoscritto, dopo aver visto i dati | utente |
| 2026-09-29 | §11 | **GLMM** stimato solo con almeno 3 trial **con eventi** (il §11 dice «k ≥ 3») | un GLMM su trial a doppio zero non è informativo; registrata nel §15 dopo la verifica del lavoro di metodo | utente |
| 2026-10-01 | §12 | **Discordanze GRADE decise dall'utente in ritardo**: le 4 discordanze fra i passaggi A e B (S2 e S6 estesa indirettezza, S7 primaria incoerenza e imprecisione) erano state risolte dall'agente nel consenso del 2026-09-29 senza decisione dell'utente, contro `grade-meta.md` §6; l'utente le ha decise il 2026-10-01 confermando il consenso in tutte e quattro (`99-Meta/log/grade/decisioni-utente-2026-10-01.md`); nessun giudizio né livello di certezza cambia | segnalato dal fact-check dell'abstract del lavoro di metodo, dopo la stesura dei manoscritti | utente |

## 16. Registro delle versioni

| Versione | Data | Nota |
|---|---|---|
| 0.1-bozza | 2026-09-29 | Prima bozza, punti ⟦DA DECIDERE⟧ aperti |
| 0.2-bozza | 2026-09-29 | Decisi: solo adulti, crossover solo primo periodo, soglia 0,65 confermata, soglia per difetto con sensibilità, S4 mantenuto, S8 opzione (c), Embase via utente, Consensus supplementare |
| 0.3-bozza | 2026-09-29 | Soglia primaria verificata su PHOSPHARE-IDA (PMID 32016310) |
| 0.4-bozza | 2026-09-29 | §7.1: nessun limite anteriore in nessuna fonte; vincolo di build_term() e controllo bloccante sulla querytranslation |
| 1.0 | 2026-09-29 | Congelato. §7.1 aggiornato con l'attuazione tecnica e la prova a vuoto |
