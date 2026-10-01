---
tipo: meta
descrizione: Criteri operativi di selezione per la meta-analisi degli RCT testa a
  testa FDI vs FCM. Derivano dal protocollo v1.0 (§4, §5, §8) e valgono solo per
  il corpus `meta`. Non sostituiscono criteri-screening.md, che resta del wiki.
versione: 1.2
---

# Criteri di selezione — meta-analisi FDI vs FCM

> [!note] Versione 1.0, approvata il 2026-09-29. In caso di conflitto prevale il protocollo (`protocollo-metanalisi.md` v1.0):
> questo file lo rende operativo, non lo modifica.

## Domanda

> Negli adulti con carenza marziale, un RCT ha randomizzato direttamente dei
> pazienti a ferro derisomaltosio (FDI) e a ferro carbossimaltosio (FCM)?

Tutto il resto (esiti riportati, dosi, durata, popolazione clinica) **non** è un
criterio di selezione. Serve all'estrazione e alle analisi.

## Due fasi, due domande diverse

| Fase | Colonne DB | Sulla base di | Chi decide | Soglia |
|---|---|---|---|---|
| 1. Titolo e abstract | `stato_screening_meta`, `motivo_screening_meta` | titolo, abstract, publication type | agente di screening; i `dubbio` li decide l'utente | **larga**: si esclude solo ciò che è certamente fuori |
| 2. Eleggibilità | `stato_eleggibilita_meta`, `motivo_eleggibilita_meta` | fulltext (o registro, o abstract congressuale se è tutto ciò che esiste) | **l'utente**, su ogni record (protocollo §8.3) | **stretta**: tutti i criteri verificati sul testo |

In fase 1 un errore per eccesso costa una lettura in più. Un errore per
difetto perde un trial per sempre. Per questo nel dubbio si passa alla fase 2.

## Fase 1 — titolo e abstract

### Incluso (passa alla fase 2)

Il record **potrebbe** riportare dati da un RCT con un braccio FDI e un braccio
FCM randomizzati fra loro. Rientrano:

- la pubblicazione primaria di un RCT testa a testa;
- analisi secondarie, post-hoc e follow-up di un RCT testa a testa, anche se
  l'abstract non nomina esiti del protocollo: sono pubblicazioni dello stesso
  trial e possono contenere dati per braccio (§5);
- RCT a più bracci in cui FDI e FCM sono due dei bracci;
- abstract congressuali e lettere con dati originali di un RCT testa a testa;
- record in lingua diversa dall'inglese, se titolo o abstract lasciano aperta
  la possibilità;
- **record senza abstract** il cui titolo non esclude con certezza la domanda:
  si decide sul fulltext.

### Registrazioni di trial e abstract congressuali

- Una **registrazione** (ClinicalTrials.gov, EU CTR, CTIS, ICTRP) si valuta come
  un record qualunque: se descrive un trial con bracci FDI e FCM assegnati per
  randomizzazione è `incluso`, **anche senza risultati**. Lo stato `in-attesa`
  si decide in fase 2, non qui. Uno studio registrato come osservazionale è `E1`.
- Un **abstract congressuale** con dati di un RCT FDI vs FCM è `incluso`, anche
  se il trial è già noto: è un'altra pubblicazione dello stesso trial (§5).

### Dubbio (decide l'utente)

- non si capisce se l'assegnazione a FDI o FCM sia stata randomizzata
  (es. «patients received FDI or FCM»);
- non si capisce se la popolazione sia adulta;
- sembra un'analisi di più trial (pooled) che potrebbe includere un RCT testa a
  testa non pubblicato altrove.

### Escluso — codici

Il motivo comincia **sempre** con il codice, seguito da una frase concreta.

| Codice | Quando | Esempio |
|---|---|---|
| `E1-non-randomizzato` | coorte, caso-controllo, serie, case report, analisi di database, studio osservazionale, anche se confronta FDI e FCM | coorte retrospettiva FDI vs FCM |
| `E2-manca-FDI-o-FCM` | uno dei due farmaci non c'è come braccio randomizzato | RCT FCM vs ferro orale; RCT FDI vs iron sucrose |
| `E3-non-primario` | review narrativa, revisione sistematica, meta-analisi, editoriale, commento, linea guida, lettera senza dati propri, **modello economico** (costo-utilità, budget impact, anche se usa dati di un RCT) | meta-analisi FDI vs FCM; analisi costo-utilità |
| `E4-non-umano` | studio animale, in vitro, di formulazione | stabilità del complesso ferro-carboidrato |
| `E5-pediatrico` | popolazione interamente o prevalentemente < 18 anni (protocollo §4) | RCT in pediatria |
| `E6-cosomministrazione` | FDI o FCM somministrati insieme a un altro ferro EV nello stesso braccio | |
| `E7-errata` | erratum, ritrattazione | |

Le revisioni e le meta-analisi escluse con `E3` si annotano anche in
`fonti-di-riferimenti.md`: i loro riferimenti servono alla ricerca per citazione
(protocollo §7).

**Protocolli di trial senza risultati** (pubblicati in rivista o come record di
registro) che descrivono un RCT testa a testa: **passano la fase 1** come
`incluso`, con motivo che comincia per «protocollo». In fase 2 ricevono lo
stato `in-attesa` («studi in attesa di classificazione» del PRISMA 2020), non
`escluso`. Servono al §11 del protocollo (trial registrati vs pubblicati) e
vengono rivalutati a ogni aggiornamento della ricerca. Deciso il 2026-09-29.

## Fase 2 — eleggibilità sul fulltext

Tutti e cinque i criteri devono essere verificati **sul testo**, non dedotti:

1. **Randomizzazione** fra un braccio FDI e un braccio FCM. Sono esclusi i
   quasi-randomizzati (alternanza, data di nascita, numero di cartella) e le
   estensioni open-label senza nuova randomizzazione.
2. **Farmaci**: FDI (compreso *iron isomaltoside 1000*, Monofer, Monoferric) e
   FCM, per via endovenosa, a qualsiasi dose e schema.
3. **Adulti**: ≥ 18 anni. Trial misti inclusi solo se i dati degli adulti sono
   separabili, oppure se i minori sono meno del 10% dei randomizzati; la
   condizione va dichiarata nel motivo.
4. **Carenza marziale**, con o senza anemia, di qualsiasi eziologia.
5. **Crossover**: incluso, ma si usa solo il primo periodo. Se il primo periodo
   non è pubblicato separatamente, il trial è incluso nella revisione e non
   entra nelle analisi aggregate: lo si scrive nel motivo.

**Non si esclude per gli esiti.** Un trial eleggibile che non riporta nessuno
degli esiti del §6 resta incluso nella revisione. Non contribuisce alle stime e
lo si dichiara. Escluderlo nasconderebbe un possibile bias di reporting degli
esiti.

Codici di esclusione in fase 2: gli stessi della fase 1, più:

| Codice | Quando |
|---|---|
| `E9-quasi-randomizzato` | assegnazione non casuale dichiarata nei metodi |
| `E10-popolazione` | non è carenza marziale, oppure non si separano gli adulti |
| `E11-duplicato` | stesso rapporto già presente con altro identificativo (non una pubblicazione secondaria: quella si collega al trial) |
| `E12-fulltext-irreperibile` | nessun fulltext, registro o abstract utilizzabile dopo tutti i canali; il record resta elencato nel PRISMA |

Stato `in-attesa` (non è un'esclusione): protocollo o registrazione di un RCT
testa a testa senza risultati disponibili, oppure trial concluso senza dati per
braccio accessibili. Motivo obbligatorio, che comincia con `A-protocollo` o
`A-senza-risultati`.

### Volumi di abstract congressuali

Un volume intero di abstract (supplemento o raccolta di poster) non è la
pubblicazione di un trial. In fase 2:

1. si cerca nel volume l'abstract che confronta FDI e FCM;
2. se c'è, lo si registra come record a sé, con il proprio identificativo
   (DOI dell'abstract se esiste, altrimenti `<id-volume>-<codice-abstract>`),
   con nota del volume di provenienza; il volume esce con `E11-duplicato`
   rimandando al nuovo record;
3. si valuta quell'abstract, non il volume;
4. se il volume non contiene nessun abstract pertinente, è escluso con
   `E3-non-primario: volume senza abstract FDI vs FCM` e il nome del congresso.

Più abstract pertinenti nello stesso volume danno più record.

### Dopo l'inclusione

Ogni record incluso in fase 2 si collega al suo trial in `trial_pubblicazione`,
con ruolo `primaria` o `secondaria`. Il lint segnala un incluso senza trial
(protocollo §5).

## Esecuzione

- Blocchi di 25 record, come per il wiki.
- **Doppio screening indipendente in fase 1** (deciso il 2026-09-29, deviazione
  registrata nel protocollo §15). Due passaggi del `meta-screener` (A e B) sugli
  stessi blocchi, senza che l'uno veda l'altro. `scripts/screening_meta.py
  --confronta` scrive in DB le decisioni concordi; ogni discordanza, e ogni
  `dubbio` di almeno un passaggio, diventa `dubbio` con i due motivi affiancati e
  la decide l'utente. I JSON grezzi di A e B si conservano in
  `99-Meta/log/screening-meta/`, e lo script calcola l'accordo (kappa di Cohen)
  da riportare nel lavoro.
- Il subagent `triage-screener` legge i criteri del wiki e **non** si usa qui.
  Per la meta-analisi c'è `meta-screener` (`.claude/agents/meta-screener.md`),
  che legge questo file.
- Le decisioni si scrivono in DB solo con uno script, mai a mano.

## Registro delle versioni

| Versione | Data | Nota |
|---|---|---|
| 0.1-bozza | 2026-09-29 | Prima bozza dal protocollo v1.0 |
| 1.0 | 2026-09-29 | Decisi: protocolli senza risultati → `in-attesa`; doppio screening indipendente in fase 1 |
| 1.1 | 2026-09-29 | Chiarimenti, dopo lo screening dei 147 PubMed e prima di quello delle altre fonti: registrazioni e abstract congressuali; modelli economici → `E3`. Nessuna decisione precedente cambia |
| 1.2 | 2026-09-29 | Regola dei volumi di abstract congressuali in fase 2, decisa dall'utente |
