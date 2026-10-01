---
tipo: meta
descrizione: Codebook dell'estrazione per braccio della meta-analisi FDI vs FCM
  (protocollo v1.0, §5, §6, §9). Definisce i due CSV, i vocabolari controllati e
  le regole. Lo usano l'agente meta-estrattore e scripts/estrazione_meta.py.
versione: 1.2
---

# Codebook dell'estrazione — meta-analisi FDI vs FCM

> [!note] Versione 1.2, 2026-09-29: chiarimenti dopo il pilota PHOSPHARE-IBD
> (1.1) e dopo PHOSPHARE-IDA04/05 (1.2, §6 regole 8-10). La 1.0 è stata approvata dall'utente lo stesso giorno.

## 1. Principi

- **Nessun numero senza sede.** Ogni riga ha `pagina_o_tabella` e una citazione
  breve in `citazione`: chi rilegge deve trovare il numero in meno di un minuto.
- **Si trascrive, non si calcola.** Numeratori, denominatori, medie e DS si
  copiano come riportati. Una percentuale senza numeratore si trascrive in
  `percentuale` e **non** si converte in eventi (lo fa, se ammesso, la fase di
  consenso, dichiarandolo).
- **Una riga per fonte.** Se lo stesso esito compare in più pubblicazioni dello
  stesso trial (primaria, secondaria, registro), si estrae una riga per ciascuna.
  Quale riga entra nell'analisi lo decide la regola del §5 del protocollo in fase
  di consenso (`usa_in_analisi`), non l'estrattore.
- **Solo i bracci FDI e FCM.** Nei trial a più bracci gli altri bracci non si
  estraggono.
- **Il silenzio non è uno zero.** Un esito non riportato non genera righe con
  zero eventi. Uno zero si scrive solo se la fonte dice zero.

## 2. `30-Dati/ma-bracci.csv` — dati per braccio

Una riga per trial × fonte × braccio × esito × finestra × soglia.

| Colonna | Contenuto | Vocabolario / formato |
|---|---|---|
| `trial_id` | come nella tabella `trial` del DB | es. `NCT03238911` |
| `pmid` | record da cui viene il dato | PMID o identificativo del corpus meta |
| `braccio` | etichetta del braccio come nella fonte | testo |
| `farmaco` | | `FDI` \| `FCM` |
| `dose_totale_mg` | dose cumulativa pianificata o somministrata (dirlo in `note`). **Solo se è un valore unico** per tutto il braccio; se dipende da peso o Hb resta vuota e l'intervallo va in `note` (es. «dose cumulativa 1500 o 2000 mg secondo Hb e peso») | numero |
| `schema` | | es. `1000 d0`; `750 d0 + 750 d7` |
| `n_randomizzati` | randomizzati nel braccio. È un dato del trial: si scrive in **ogni** riga, anche se la fonte di quella riga non lo riporta, prendendolo dalla primaria o dal registro e citandolo in `note` | intero |
| `n_analizzati` | denominatore dell'esito in questa riga | intero |
| `popolazione_analisi` | a cosa si riferisce `n_analizzati` | `randomizzati` \| `safety` \| `itt` \| `mitt` \| `per-protocol` \| `altro` |
| `esito` | codice dell'esito (§3) | `P1` `S1` `S2` `S3` `S4` `S5` `S6` `S7` `S8a` `S8b` |
| `finestra` | `primaria` solo se il dato si riferisce a un periodo che finisce entro 35 ± 7 giorni dalla prima dose; **eventi avversi contati sull'intero follow-up** (es. giorni 0-70) sono sempre `estesa` | `primaria` \| `estesa` |
| `soglia_mmol_l` | soglia usata dalla fonte, convertita (§4) | numero, 2 decimali; vuoto se non pertinente |
| `soglia_testo` | soglia come scritta nella fonte | es. `<2.0 mg/dL` |
| `n_eventi` | pazienti con l'evento | intero; vuoto se non riportato |
| `percentuale` | solo se la fonte dà la % senza numeratore | numero |
| `media` | S4: valore centrale | numero |
| `ds` | S4: dispersione | numero |
| `tipo_dispersione` | | `ds` \| `es` \| `ic95` \| `iqr` \| `range` |
| `misura_continua` | S4 | `nadir` \| `variazione-da-basale` \| `valore-a-tempo` |
| `unita` | S4 | `mmol/L` \| `mg/dL` |
| `tempo_misura_giorni` | giorno a cui si riferisce il dato | intero o intervallo `0-35` |
| `pagina_o_tabella` | sede precisa | es. `Table 2`; `Results p. 437`; `resultsSection.outcomeMeasures[0]` |
| `citazione` | frase o riga di tabella, ≤ 200 caratteri | testo tra virgolette basse |
| `fonte_dato` | | `fulltext` \| `supplementare` \| `registro` \| `abstract` |
| `estrattore` | | `A` \| `B` \| `consenso` |
| `usa_in_analisi` | deciso in consenso | `si` \| `no` \| vuoto |
| `note` | | testo |

## 3. Esiti (protocollo §6)

| Codice | Esito | Tipo | Definizione operativa |
|---|---|---|---|
| `P1` | Ipofosfatemia | dicotomico | fosfato < 0,65 mmol/L (< 2,0 mg/dL) in almeno una misurazione nella finestra |
| `S1` | Ipofosfatemia grave | dicotomico | fosfato ≤ 0,32 mmol/L (≤ 1,0 mg/dL) |
| `S2` | Ipofosfatemia a soglia larga | dicotomico | fosfato < 0,80 mmol/L (< 2,5 mg/dL); 0,81 si registra qui con la soglia vera |
| `S3` | Ipofosfatemia persistente | dicotomico | < 0,65 mmol/L all'ultima visita della finestra primaria |
| `S4` | Fosfato continuo | continuo | nadir, variazione dal basale o valore a un tempo, con `misura_continua` |
| `S5` | Osteomalacia / fratture | dicotomico | come riportate; zero solo se dichiarato |
| `S6` | Ipersensibilità grave | dicotomico | anafilassi o HSR grave/seria (NIAID/FAAN, WAO, Ring & Messmer ≥ II, SAE della SMQ *Anaphylactic reaction*): la definizione usata va in `note` |
| `S7` | Ipersensibilità, qualsiasi | dicotomico | qualsiasi HSR o reazione infusionale come classificata dalla fonte |
| `S8a` | Eventi CV aggiudicati | dicotomico | composito o eventi CV aggiudicati dal trial |
| `S8b` | SAE cardiaci e vascolari | dicotomico | SAE delle SOC *Cardiac disorders* + *Vascular disorders* |

Le righe con un esito ma senza dati utilizzabili non si scrivono: se una fonte
dice solo «nessuna differenza», lo si annota in `ma-trial.csv`, colonna `note`.

## 4. Soglie e conversioni

- mg/dL → mmol/L: × 0,3229, arrotondato a 2 decimali (2,0 → 0,65; 2,5 → 0,81;
  1,0 → 0,32). La soglia originale va sempre in `soglia_testo`.
- **Soglia non coincidente** (protocollo §6.4): la riga si registra con la soglia
  vera; l'assegnazione all'esito più vicino per difetto e l'analisi di
  sensibilità le fa lo script, non l'estrattore.
- `<` e `≤` si trascrivono come nella fonte in `soglia_testo`.

## 5. `30-Dati/ma-trial.csv` — caratteristiche dei trial

Una riga per trial.

| Colonna | Vocabolario / formato |
|---|---|
| `trial_id`, `acronimo` | come nel DB |
| `registri` | tutti i numeri, separati da `;` |
| `disegno` | es. `parallelo 1:1`; `3 bracci 1:1:1` |
| `cecita` | `open-label` \| `singolo` \| `doppio` \| `non-riportato` |
| `paese`, `n_centri` | |
| `popolazione` | una riga |
| `criterio_ferro` | es. `Hb ≤11 g/dL e ferritina ≤100 ng/mL` |
| `criterio_fosfato_basale` | es. `fosfato normale richiesto`; `non riportato` |
| `n_randomizzati_totale`, `n_randomizzati_fdi`, `n_randomizzati_fcm` | interi |
| `eta_media`, `pct_donne` | come riportati, con la misura (`media`/`mediana`) in `note` |
| `dose_fdi`, `dose_fcm` | schema come nella fonte |
| `follow_up_giorni` | ultima visita |
| `esito_primario_registrato` | come nel registro, o `nessun registro` |
| `sponsor`, `finanziamento` | `industriale` \| `pubblico` \| `misto` \| `non-dichiarato` \| `nessuno` |
| `produttore_coinvolto` | `pharmacosmos` \| `vifor` \| `entrambi` \| `nessuno` \| `non-dichiarato` |
| `conflitti` | `si` \| `no` \| `non-dichiarati` |
| `pmid_fonti` | record letti, separati da `;` |
| `pagina_o_tabella`, `citazione`, `estrattore`, `note` | come sopra |

## 6. Regole emerse dal trial pilota (v1.1)

1. **Supplementi prima dell'estrazione.** Per ogni pubblicazione open access si
   recuperano i materiali supplementari (Europe PMC `supplementaryFiles`) e si
   salvano come `90-Sorgenti/fulltext/<id>-suppl.md` (PDF in
   `90-Sorgenti/pdf/<id>-suppl.pdf`) **prima** di lanciare gli estrattori. In
   PHOSPHARE-IBD il supplemento conteneva S3 e le analisi di sensibilità.
2. **Analisi di sensibilità.** Una riga di sensibilità ha la `note` che
   **comincia** con `sensibilità:` seguita da un'etichetta breve (es.
   `sensibilità: persi al follow-up esclusi`). Solo quel prefisso la identifica:
   la parola altrove nella nota non conta.
3. **S3 solo sulla finestra primaria.** L'ipofosfatemia a visite successive si
   può trascrivere come `S3` in finestra `estesa`, ma non entra nell'analisi
   principale.
4. **S8b da registri che riportano per termine (PT) e non per SOC.** Il numero
   di pazienti per SOC si può scrivere solo se, in quel braccio, un solo PT della
   SOC ha pazienti: allora il conteggio per paziente è esatto. Altrimenti niente
   riga, e il motivo va nella `note` della riga `trial`.
5. **Denominatori dei registri.** Nelle schede di risultati i denominatori degli
   esiti sono quelli del set di analisi, non i randomizzati: `n_analizzati` e
   `popolazione_analisi` li riportano come sono.
6. **Endpoint prespecificati non riportati.** Se la Table degli endpoint o il
   registro elencano un esito del codebook senza risultati, lo si scrive nella
   `note` della riga `trial` («endpoint prespecificato non riportato: …»): serve
   al giudizio RoB 2 sul reporting selettivo.
7. **Integrazioni successive.** Se una fonte arriva dopo l'estrazione, entrambi
   i passaggi la integrano nel proprio file, in modo indipendente; le righe già
   scritte non si toccano e le note superate si correggono in consenso.

8. **Follow-up breve.** Se il follow-up del trial termina entro 35 ± 7 giorni
   dalla prima dose, gli eventi avversi contati sull'intero follow-up stanno in
   finestra `primaria`, non `estesa`.
9. **Zeri da elenchi completi di eventi seri.** Nelle schede di risultati di
   ClinicalTrials.gov l'elenco degli eventi avversi seri non ha soglia di
   frequenza: se nessun evento serio di una SOC compare per un braccio, lo zero
   di S8b per quella SOC si scrive, con la nota «zero dedotto dall'elenco
   completo degli SAE». Non vale per gli eventi non seri (elencati sopra una
   soglia, di solito il 5%) né per registri senza elenco completo.
10. **Denominatori per visita.** Se il denominatore è il numero di pazienti con
    misura a una visita, `popolazione_analisi` = `altro` anche quando il
    registro lo chiama «safety analysis set»; l'etichetta del registro va in
    `note`.

## 7. Procedura

0. Recupero dei supplementi (§6.1).
1. Due estrazioni indipendenti per trial (agente `meta-estrattore`, passaggi A e
   B), scritte in file separati.
2. `scripts/estrazione_meta.py --confronta` allinea le righe per chiave
   (trial, fonte, farmaco, esito, finestra, soglia) e segnala ogni cella diversa
   e ogni riga presente in un solo passaggio.
3. L'utente decide le discordanze e **verifica sul PDF ogni riga** con
   `usa_in_analisi = si` (protocollo §9).
4. `--unisci` scrive le righe di consenso in `30-Dati/`, con `estrattore = consenso`.

## Registro delle versioni

| Versione | Data | Nota |
|---|---|---|
| 1.0 | 2026-09-29 | Approvata dall'utente |
| 1.1 | 2026-09-29 | Chiarimenti dal pilota PHOSPHARE-IBD: dose cumulativa, randomizzati in ogni riga, finestra degli eventi avversi, §6 regole 1-7 |
| 1.2 | 2026-09-29 | Da PHOSPHARE-IDA04/05, approvate dall'utente: follow-up breve, zeri da elenchi completi di SAE, denominatori per visita (§6 regole 8-10) |
