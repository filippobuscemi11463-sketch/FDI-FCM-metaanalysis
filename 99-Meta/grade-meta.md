---
tipo: meta
descrizione: Guida operativa a GRADE per la meta-analisi FDI vs FCM (protocollo
  §12). Definisce i criteri di declassamento, le regole specifiche del vault,
  il CSV 50-Metanalisi/grade.csv, la tabella Summary of Findings e le frasi
  di sintesi. La usano l'agente di valutazione e lo script di analisi.
versione: "1.0"
---

# GRADE — guida operativa

> [!note] Versione 1.0, approvata dall'utente il 2026-09-29.

## 1. Principi

- **Per esito e finestra**, sul risultato principale di
  `50-Metanalisi/output/risultati.csv`. Le analisi affiancate e di
  sensibilità informano i giudizi, ma non hanno un GRADE proprio.
- **Punto di partenza: certezza alta.** Tutti gli studi sono RCT. Non si
  alza mai la certezza: i criteri per alzarla (effetto grande,
  dose-risposta, confondimento residuo) valgono per gli studi osservazionali.
- **Cinque domini di declassamento**, ciascuno 0, −1 o −2: rischio di bias,
  incoerenza, indirettezza, imprecisione, bias di pubblicazione.
- **Certezza finale:** alta (0), moderata (−1), bassa (−2), molto bassa (≤ −3).
- **Ogni giudizio ha una motivazione scritta** che cita i dati da cui nasce:
  una riga di `risultati.csv` o di `trial-singoli.csv`, un giudizio di
  `30-Dati/ma-rob2.csv` o una nota di consenso. Nessun numero nuovo: tutti i
  numeri vengono dagli output dello script.
- **Esiti senza stima aggregata** (sintesi narrativa: P1 estesa, S2, S6
  estesa, S7, S8b) ricevono comunque un GRADE, con gli stessi domini
  applicati ai trial affiancati (approccio narrativo, Murad 2017).
- **Esiti senza dati** (S5, S8a): «nessuna evidenza dagli RCT testa a
  testa». Nessun giudizio di certezza.

## 2. Domini

### 2.1 Rischio di bias

Si parte dai giudizi complessivi di `ma-rob2.csv` per quell'esito, pesati
secondo il contributo dei trial alla stima. Il peso è quello del modello
principale; per le sintesi narrative, la numerosità.

- **0** se i trial con la maggior parte del peso sono a rischio `basso`.
- **−1** se la maggior parte del peso viene da trial con
  `alcune-preoccupazioni`, oppure se i trial ad `alto` rischio pesano meno
  della metà.
- **−2** se la maggior parte del peso viene da trial ad `alto` rischio.

Le segnalazioni per GRADE scritte nelle note di consenso di `ma-rob2.csv` si
discutono qui. È il caso, per esempio, di HOMe aFers, fermato all'analisi ad
interim con possibile sovrastima dell'effetto. Si discutono anche se non
cambiano il punteggio.

### 2.2 Incoerenza

- **0** se le stime dei trial vanno nella stessa direzione e gli IC si
  sovrappongono, anche con I² alto. Un I² alto con effetti tutti dalla stessa
  parte non basta a declassare.
- **−1** se ci sono direzioni opposte o IC che non si sovrappongono, senza una
  spiegazione (popolazione, dose, definizione).
- **−2** se l'incoerenza è marcata e riguarda trial con peso rilevante.
- Con k = 1 l'incoerenza **non è valutabile**. Non si declassa, e lo si
  scrive.

### 2.3 Indirettezza

Si confronta la domanda PICO del protocollo (§4) con i trial. I motivi di
declassamento sono:
- una popolazione diversa da quella della domanda. Una popolazione ristretta
  (IBD, CKD, gravidanza) da sola **non** basta, perché la domanda riguarda gli
  adulti con carenza di ferro in generale;
- una definizione dell'esito diversa da quella del protocollo, cioè una
  soglia non esatta (§6.4);
- una misurazione che non coglie l'esito. È il caso di Lubiana: fosfato
  misurato solo a 6 settimane, quindi l'ipofosfatemia transitoria sfugge;
- schemi di dose non confrontabili.

**Regola del vault:** P1–S4 sono esiti di laboratorio e sono **l'esito
stesso della domanda**, non surrogati. Non si declassano per surrogatezza.
Il legame con le conseguenze cliniche (S5) si discute in una nota a margine,
non nel punteggio.

### 2.4 Imprecisione

**Soglia di decisione (decisa dall'utente):** approccio *minimamente
contestualizzato*, con la soglia sull'assenza di effetto (RR = 1, RD = 0,
MD = 0). Si giudica la certezza che un effetto esista e abbia quella
direzione. Motivo: per il fosfato e per le reazioni di ipersensibilità non
esistono nel vault differenze minime importanti fondate su una fonte, e
inventarle violerebbe CLAUDE.md §9.

- **0** se l'IC 95% non attraversa la soglia **e** si raggiunge la
  dimensione informativa ottimale. Come orientamento: ≥ 300 eventi totali
  per i dicotomici, ≥ 400 partecipanti per i continui.
- **−1** se l'IC attraversa la soglia, oppure se non la attraversa ma la
  dimensione informativa ottimale non è raggiunta.
- **−2** se l'IC è molto ampio: comprende sia un effetto relativo
  importante a favore di un farmaco sia uno a favore dell'altro. Come
  orientamento, un RR che include sia 0,5 sia 2 con pochi eventi.
- **Esiti a zero eventi o quasi** (S6, S8b): −2 di regola. L'assenza di
  eventi non dimostra l'assenza di effetto.

### 2.5 Bias di pubblicazione

Il funnel plot non si fa, perché k < 10 per tutti gli esiti (protocollo §11).
Si valutano:
- **trial registrati senza risultati:** IVORY (NCT06350955) è `in-attesa` e
  non ancora concluso, quindi non conta come trial mancante;
- **completezza della ricerca:** le ricerche manuali in Embase, CENTRAL e
  ICTRP non sono ancora state fatte (limite dichiarato nel log della ricerca);
- **concentrazione dei finanziamenti:** tutti i trial di P1, S3 e S4 sono
  finanziati da Pharmacosmos, produttore di FDI.

**Regola (decisa dall'utente):**
- **0** con la motivazione esplicita dei tre punti, e una nota a margine
  sul finanziamento. Il finanziamento di per sé non è un bias di
  pubblicazione: il bias nasce se trial sfavorevoli restano inediti, e non
  ce n'è prova;
- il giudizio è **provvisorio** finché non si fanno le ricerche in Embase,
  CENTRAL e ICTRP;
- **−1** solo con prove specifiche, per esempio un trial concluso da oltre
  due anni senza risultati.

## 3. `50-Metanalisi/grade.csv`

Una riga per esito × finestra con risultato principale.

| Colonna | Contenuto |
|---|---|
| `esito`, `finestra` | come in `risultati.csv` |
| `k`, `partecipanti` | trial e partecipanti della stima principale (dallo script) |
| `rischio_bias`, `incoerenza`, `indirettezza`, `imprecisione`, `pubblicazione` | 0, −1 o −2 |
| `motivo_<dominio>` | una frase per dominio, con i riferimenti ai dati |
| `certezza` | `alta` \| `moderata` \| `bassa` \| `molto-bassa` \| `nessuna-evidenza` |
| `frase` | frase di sintesi (§5) |
| `valutatore` | `A` \| `B` \| `consenso` |

La certezza la ricalcola uno script dalla somma dei punteggi: una certezza
scritta a mano diversa da quella calcolata è un errore di validazione.

## 4. Summary of Findings

La tabella SoF (`50-Metanalisi/sof.md`) la genera lo script da
`risultati.csv` e `grade.csv`. Colonne:
- esito;
- trial (partecipanti);
- rischio con FCM, cioè il rischio grezzo aggregato dei bracci FCM dei trial
  nella stima;
- rischio con FDI, cioè il rischio FCM × l'effetto relativo, per 1000;
- differenza per 1000 con IC;
- effetto relativo con IC;
- certezza;
- frase.

Per le sintesi narrative, la tabella riporta gli eventi per trial al posto
dell'effetto aggregato.

**Nota:** per i rischi assoluti bisogna estendere lo script di analisi (§11:
nessun numero aggregato scritto a mano). Si fa dopo l'approvazione di questa
guida.

## 5. Frasi di sintesi

Formulazione standard GRADE (Santesso 2020), in italiano, senza indicazioni
terapeutiche (CLAUDE.md §9):

| Certezza | Formula |
|---|---|
| alta | «FDI riduce / aumenta …» |
| moderata | «FDI probabilmente riduce …» |
| bassa | «FDI potrebbe ridurre …» |
| molto bassa | «L'evidenza è molto incerta sull'effetto di FDI su …» |
| effetto vicino a nullo | «… fa poca o nessuna differenza …» |

Il confronto è sempre «FDI rispetto a FCM».

## 6. Procedura

**Decisa dall'utente:** come per RoB 2, **due valutazioni indipendenti**
(agenti A e B) dei 12 esiti × finestra. Poi un confronto automatico, le
discordanze decise dall'utente e il consenso in `grade.csv`.

## Registro delle versioni

| Versione | Data | Nota |
|---|---|---|
| 1.0 | 2026-09-29 | Prima stesura, dal protocollo §12 e dalle segnalazioni raccolte in RoB 2; approvata dall'utente |
