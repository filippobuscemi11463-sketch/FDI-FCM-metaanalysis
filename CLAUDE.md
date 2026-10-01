# CLAUDE.md — FDI-FCM-Wiki

Wiki LLM in stile Karpathy su **farmacocinetica ed eventi avversi del ferro
derisomaltosio (FDI) e del ferro carbossimaltosio (FCM)**, e sul loro confronto.

Questo file è il contratto operativo del vault. Leggilo per intero all'inizio di
ogni sessione. Se una regola qui confligge con un'abitudine generale, **vince
questo file**.

---

## 1. Scopo e principio guida

Il vault serve a rispondere, con evidenza tracciabile al singolo dato, a tre
domande:

1. **Come si comportano FDI e FCM in vivo** (cinetica del ferro, rilascio,
   clearance, ferro non legato a transferrina, effetto su FGF23 e fosforemia).
2. **Quali eventi avversi producono, con quale frequenza e in quale popolazione**
   (ipofosfatemia, ipersensibilità/anafilassi, reazione di Fishbane, eventi
   cardiovascolari, ipertensione, altro).
3. **Come si confrontano fra loro**, e con gli altri ferri EV usati come
   comparatori.

**Principio guida — nessun numero senza fonte.** Ogni dato quantitativo scritto
in una nota di sintesi deve essere accompagnato dal PMID e dalla sede precisa
nel sorgente (sezione, tabella, figura). Se il dato viene dall'abstract e non dal
fulltext, va marcato `(abstract)`. Un dato senza provenienza è un errore di
lint, non una svista.

**Distinzione non negoziabile fra dato riportato e inferenza.** Le note di
sintesi separano fisicamente ciò che gli studi dicono da ciò che tu concludi:
l'inferenza sta sempre in un blocco `> [!inferenza]`, mai mescolata al dato.

---

## 2. Perimetro della ricerca

Finestra temporale: **ultimi 5 anni mobili** rispetto alla data di esecuzione
(oggi meno 5 anni). La finestra è calcolata dagli script, non scritta a mano.
Vale per il corpus del wiki. Il corpus `meta` (colonna `corpus` in
`state.sqlite`, query `M1-rct-head-to-head`) non ha finestra temporale e
segue solo il protocollo `99-Meta/protocollo-metanalisi.md`.

Farmaci in scope, con tutti i sinonimi commerciali e storici:

| Molecola | Sinonimi da cercare |
|---|---|
| Ferro derisomaltosio (**FDI**) | ferric derisomaltose, iron isomaltoside, iron isomaltoside 1000, Monofer, Monoferric, Diafer |
| Ferro carbossimaltosio (**FCM**) | ferric carboxymaltose, carboxymaltose, Ferinject, Injectafer |
| Comparatori EV | ferumoxytol (Feraheme, Rienso), ferro saccarato / iron sucrose (Venofer), ferro gluconato, ferric gluconate, low molecular weight iron dextran (CosmoFer, INFeD), ferric maltol (orale, solo se braccio di confronto) |

**Nota storica importante:** *iron isomaltoside 1000* e *ferric derisomaltose*
sono la stessa molecola. Il cambio di denominazione INN è avvenuto nel 2019: la
letteratura pre-2020 usa quasi esclusivamente il nome vecchio, che resta
presente anche in pubblicazioni recenti. Una query che omette il sinonimo
storico perde studi. Non ometterlo mai.

### Tipologie incluse

Solo **lavori originali**: RCT, studi di coorte prospettici e retrospettivi,
caso-controllo, studi di farmacocinetica, analisi post-hoc e pooled analysis di
trial, studi di farmacovigilanza su database (FAERS, EudraVigilance, VigiBase,
registri nazionali), case report e case series di reazioni avverse.

### Tipologie escluse

Review narrative, revisioni sistematiche, meta-analisi, editoriali, commenti,
news, linee guida, errata corrige, ritrattazioni.

> Le meta-analisi **non entrano nel corpus** ma possono essere consultate come
> *fonte di riferimenti* per il controllo di completezza (vedi §8). In quel caso
> non si crea una nota paper: si annota il PMID in
> `99-Meta/fonti-di-riferimenti.md`.

**Attenzione al filtro `letter[pt]`.** Molti case report di reazioni avverse
sono pubblicati come lettere. Per questo `letter[pt]` **non** è nella lista di
esclusione di default (vedi `99-Meta/queries.yaml`, campo
`exclude_pubtypes`). Se il rumore diventa eccessivo, si attiva l'esclusione
solo sulle query non-farmacovigilanza, mai sulla query `Q6-farmacovigilanza`
né su `Q8-case-report`.

### Screening

Non tutto ciò che la query restituisce entra nel vault. Ogni record passa per il
subagent `triage-screener` (§6), che applica i criteri in
`99-Meta/criteri-screening.md` e assegna `stato_screening` = `incluso`,
`escluso` o `dubbio`. I `dubbio` restano in coda e li decidi tu: non
auto-risolverli.

---

## 3. Struttura del vault

```
FDI-FCM-Wiki/
├── CLAUDE.md                  ← questo file
├── 00-MOC/                    hub tematici, punto di ingresso alla lettura
├── 10-Concetti/               note atomiche concettuali (un concetto = una nota)
├── 20-Paper/                  una nota per studio incluso, nominata PMID-slug.md
├── 30-Dati/                   estrazioni strutturate in CSV (dati, non prosa)
├── 40-Sintesi/                evidence table e confronto FDI vs FCM
├── 50-Metanalisi/             meta-analisi degli RCT testa a testa (solo da protocollo):
│                              analisi.R, output/ generati, grade.csv, sof.md, grade.md
├── 90-Sorgenti/
│   ├── fulltext/              fulltext convertiti in markdown (PMID.md)
│   ├── pdf/                   PDF scaricati da fonti aperte (PMID.pdf)
│   ├── abstract/              abstract di tutti i record inclusi (PMID.md)
│   └── inbox-pdf/             ← ci metti tu i PDF recuperati a mano
├── 99-Meta/
│   ├── queries.yaml           definizione delle query PubMed
│   ├── criteri-screening.md   criteri di inclusione/esclusione operativi
│   ├── state.sqlite           stato di harvest/fulltext/ingest (fonte di verità)
│   ├── fulltext-mancanti.md   registro dei lavori senza fulltext, rigenerato
│   ├── fonti-di-riferimenti.md review/meta-analisi usate solo per completezza
│   ├── templates/             template nota paper e nota concetto
│   └── log/                   log delle run degli script
├── scripts/                   pipeline Python
└── .claude/
    ├── skills/                skill richiamabili
    └── agents/                subagent specializzati
```

**Regola sulle cartelle:** `90-Sorgenti/` è materiale grezzo, non si modifica a
mano e non si linka dalle MOC. `20-Paper/`, `10-Concetti/`, `40-Sintesi/` sono
prosa curata. `30-Dati/` sono dati macchina-leggibili. `50-Metanalisi/` contiene
solo ciò che generano gli script: non si scrivono numeri a mano. Non mescolare
i registri.

---

## 4. Lingua e stile

- **Italiano** per prosa, sintesi, MOC, note concettuali.
- **Inglese** per: nomi di farmaco e principio attivo, endpoint, nomi di scale e
  questionari, termini MedDRA, design di studio quando il termine inglese è lo
  standard (`per-protocol`, `intention-to-treat`, `open-label`), titoli degli
  studi citati.
- Unità SI. Fosforemia in **mmol/L** con conversione in mg/dL fra parentesi alla
  prima occorrenza di ogni nota. Ferritina in µg/L, TSAT in %.
- Niente linguaggio promozionale. FDI e FCM sono due molecole, non due squadre.
  Se un dato è a favore di una, si scrive; se la fonte è finanziata dal
  produttore, si scrive anche quello (campo `finanziamento` in frontmatter).
- Frasi brevi. Nessun paragrafo di riempimento.

---

## 5. Convenzioni delle note

### 5.1 Nota paper — `20-Paper/<PMID>-<slug>.md`

Slug: prime 4-5 parole significative del titolo, minuscole, trattini. Esempio:
`36102538-ferric-derisomaltose-versus-ferric-carboxymaltose.md`.

Frontmatter obbligatorio (template in `99-Meta/templates/paper.md`):

```yaml
---
tipo: paper
pmid: "36102538"
doi: "10.1001/jama.2022.xxxxx"
pmcid: ""                       # vuoto se assente
titolo: "…"
autori: "Cognome AB, et al."
anno: 2022
rivista: "…"
design: rct                     # rct | coorte-prospettica | coorte-retrospettiva |
                                # caso-controllo | pk-study | post-hoc | pooled-analysis |
                                # case-report | case-series | farmacovigilanza-db
farmaci: [FDI, FCM]
comparatori: []
popolazione: "…"                # una riga
n_totale: 0
dominio: [pk, sicurezza]        # pk | sicurezza | efficacia
outcome_estratti: [ipofosfatemia]
finanziamento: industriale      # industriale | pubblico | misto | non-dichiarato | nessuno
                                # fondazioni e società scientifiche senza legami col produttore → pubblico
conflitti_interesse: si         # si | no | non-dichiarati
fulltext: no                    # si | no | parziale
fonte_fulltext: nd              # europepmc-oa | pmc-oa | unpaywall | preprint | manuale | nd
stato_screening: incluso        # incluso | escluso | dubbio
stato_ingest: abstract-only     # abstract-only | fulltext-ingerito | da-recuperare | escluso
qualita: media                  # alta | media | bassa — giustificata in §Limiti
data_ingest: 2026-09-20
tag: []
---
```

Corpo, sempre in quest'ordine, sempre queste intestazioni:

```markdown
## In una riga
## Disegno e popolazione
## Interventi e dosi
## Risultati — farmacocinetica
## Risultati — sicurezza
## Limiti e rischio di bias
## Cosa aggiunge al confronto FDI vs FCM
## Provenienza
```

`## Provenienza` dichiara: fulltext o abstract-only; sezioni/tabelle da cui sono
presi i numeri; eventuali dati non estraibili. Se la nota è abstract-only, la
prima riga del corpo è:

```markdown
> [!warning] Nota costruita dal solo abstract — fulltext non disponibile.
> Dati da verificare al recupero del testo integrale. Vedi [[fulltext-mancanti]].
```

### 5.2 Nota concetto — `10-Concetti/<slug>.md`

Un concetto per nota, autoconsistente, 200–600 parole. Esempi di concetti
attesi: `ipofosfatemia-indotta-da-ferro-ev`, `asse-fgf23-fosfato`,
`ferro-non-legato-a-transferrina`, `reazione-di-fishbane`,
`test-dose-e-reazioni-da-ipersensibilita`, `stabilita-del-complesso-ferro-carboidrato`,
`dose-singola-massimale`, `criteri-di-definizione-ipofosfatemia`.

Ogni affermazione quantitativa cita `[[<PMID>-<slug>]]`. Le note concettuali non
introducono dati che non esistano in almeno una nota paper.

### 5.3 Collegamenti

Wikilink `[[...]]` ovunque. Ogni nota paper è linkata da almeno una MOC. Ogni
nota concetto linka almeno tre note paper. Una nota orfana è un errore di lint.

---

## 6. Pipeline operativa

La pipeline ha cinque stadi. Ciascuno ha una skill o un agent dedicato.

```
[1] harvest   → PubMed E-utilities → state.sqlite + 90-Sorgenti/abstract/
[2] screening → triage-screener    → stato_screening in state.sqlite
[3] fulltext  → fonti aperte       → 90-Sorgenti/fulltext|pdf/ + registro mancanti
[4] ingest    → paper-ingest       → 20-Paper/ + estrazioni in 30-Dati/
[5] sintesi   → 40-Sintesi/ + MOC  → fact-checker in verifica
```

### Stadio 1 — harvest

```bash
python3 scripts/pubmed_harvest.py --all          # tutte le query di queries.yaml
python3 scripts/pubmed_harvest.py --query Q1-head-to-head
python3 scripts/pubmed_harvest.py --all --dry-run   # solo conteggi, non scrive
```

Idempotente: un PMID già in `state.sqlite` non viene riscritto, viene solo
aggiornata la lista delle query che lo hanno intercettato. Gli abstract finiscono
in `90-Sorgenti/abstract/<PMID>.md`.

### Stadio 2 — screening

Richiama il subagent `triage-screener` su tutti i record `stato_screening IS
NULL`. Lavoralo **a blocchi di 25 record**, non uno alla volta: il criterio è
uniforme e il costo per record crolla. L'agent restituisce JSON; lo scrivi in DB
con `scripts/apply_screening.py`.

### Stadio 3 — fulltext

```bash
python3 scripts/fulltext_fetch.py --included      # solo i record inclusi
python3 scripts/fulltext_fetch.py --retry-failed  # ritenta i falliti temporanei
python3 scripts/fulltext_fetch.py --scan-inbox    # ingoia i PDF che hai messo a mano
```

**Regola vincolante sulle fonti.** Si scaricano fulltext **solo** da canali
aperti e leciti, nell'ordine:

1. Europe PMC REST `fullTextXML` (subset open access)
2. PMC OA Service
3. Unpaywall → `best_oa_location` (richiede `UNPAYWALL_EMAIL`)
4. Server di preprint: medRxiv / bioRxiv API, Research Square
5. Repository istituzionali indicizzati da Unpaywall

**Mai** aggirare paywall, login, proxy di ateneo non autorizzati, o siti di
pirateria bibliografica. Un articolo non ottenibile da queste fonti è, per
definizione del vault, *da recuperare manualmente*: si marca e si va avanti.
Se ti viene chiesto di recuperarlo in altro modo, rifiuta e proponi il canale
manuale.

Ogni fallimento produce una riga in `99-Meta/fulltext-mancanti.md` con PMID,
DOI, titolo, rivista, motivo (`paywall`, `nessun-DOI`, `OA-non-trovato`,
`errore-rete`) e link diretto alla pagina editore, così il recupero manuale è a
un click. Quando metti un PDF in `90-Sorgenti/inbox-pdf/` nominato `<PMID>.pdf`,
`--scan-inbox` lo converte, lo sposta in `90-Sorgenti/pdf/`, aggiorna
`fonte_fulltext: manuale` e **rimuove la riga dal registro**.

Conversione PDF → markdown: `pdftotext -layout`, poi pulizia. Se il PDF è
scansionato senza testo, marcarlo `ocr-necessario` e non tentare OCR automatico
senza chiedermelo.

### Stadio 4 — ingest

Un paper alla volta, con la skill `paper-ingest`. Per ogni paper:

1. Leggi il sorgente completo (fulltext se c'è, altrimenti abstract).
2. Scrivi la nota in `20-Paper/`.
3. Lancia `pk-extractor` e `ae-extractor` sul sorgente; le loro righe vanno nei
   CSV di `30-Dati/`, **non** riscritte a mano nella nota.
4. Aggiorna `stato_ingest` in `state.sqlite`.

**Parallelizzazione.** Quando ci sono più di 5 paper da ingerire, lancia gli
agent in parallelo, massimo 4 per volta, un paper per agent. Non lanciare due
agent sullo stesso paper.

### Stadio 5 — sintesi

Le note di `40-Sintesi/` si ricostruiscono **dai CSV di 30-Dati/**, non dalla
memoria. Dopo ogni riscrittura sostanziale, passa la nota al `fact-checker`.

---

## 7. Estrazioni strutturate

Tre CSV in `30-Dati/`. Intestazioni fisse, una riga per osservazione, mai celle
multi-valore: se un paper riporta tre dosi, sono tre righe.

**`pk.csv`** — `pmid,farmaco,dose_mg,via,n,popolazione,matrice,parametro,valore,unita,ds_o_ic,tempo,metodo_dosaggio,pagina_o_tabella,note`

`parametro` ∈ {`cmax_ferro_totale`, `cmax_ferro_libero`, `tmax`, `auc`,
`t_mezza`, `clearance`, `volume_distribuzione`, `ntbi_picco`, `tsat_picco`,
`ferritina_picco`, `fgf23_intatto_picco`, `fgf23_cterm_picco`, `fosfato_nadir`,
`fosfato_recupero_giorni`, `altro`}.

**`eventi-avversi.csv`** — `pmid,farmaco,evento,meddra_pt,n_eventi,n_esposti,percentuale,gravita,criterio_definizione,tempo_insorgenza,esito,fonte_dato,pagina_o_tabella,note`

`fonte_dato` ∈ {`fulltext`, `abstract`, `supplementare`}. Se il denominatore non
è riportato, `n_esposti` resta vuoto e la percentuale **non si calcola**.

Distinguere però due casi diversi, perché il secondo è frequente:

- **la percentuale non esiste nella fonte**: resta vuota, e si annota. Calcolarla
  a partire da un denominatore che non è quello giusto è l'errore che questa
  regola previene;
- **la percentuale esiste ma il denominatore no**, cioè è lo studio a pubblicare
  «43%» senza dire su quanti: la percentuale **si trascrive**, perché è l'unico
  numero disponibile e cancellarla perderebbe il dato. In questo caso la riga
  deve dichiarare la deroga nel campo `note` con uno di due marcatori, che
  `scripts/lint.py` riconosce:

  | Marcatore | Quando |
  |---|---|
  | `[denominatore-non-pubblicato]` | lo studio pubblica la percentuale e tace il denominatore |
  | `[denominatore-diverso-dagli-esposti]` | la percentuale è calcolata su un sottoinsieme (per esempio i soli pazienti con evento) e accostarla agli esposti sarebbe fuorviante |

  Senza marcatore il lint segnala la riga come errore. Il marcatore è una
  dichiarazione deliberata e greppabile, non una scorciatoia: non va messo su
  righe che il denominatore ce l'hanno.

**`ipofosfatemia.csv`** — `pmid,farmaco,n,soglia_mmol_l,definizione,incidenza_pct,incidenza_grave_pct,nadir_giorno,durata_mediana_giorni,fgf23_misurato,persistenza_oltre_35gg,popolazione,pagina_o_tabella,note`

Campo dedicato perché l'ipofosfatemia è il principale discriminante noto fra le
due molecole e perché **le soglie di definizione variano fra studi**: senza il
campo `soglia_mmol_l` le incidenze non sono confrontabili. Ogni confronto di
incidenze fra studi con soglie diverse va dichiarato come tale.

---

## 8. Controllo di qualità

Alla fine di ogni sessione di lavoro rigenera il dump versionato del database (`python3 scripts/dump_db.py`: `state.sqlite` è escluso da git, `99-Meta/state.sql` no) e lancia `vault-lint`. Verifica:

- ogni record `incluso` in DB ha nota in `20-Paper/`, e viceversa
- frontmatter completo e valori nei domini ammessi
- nessuna nota orfana; ogni paper linkato da ≥1 MOC
- ogni numero in `40-Sintesi/` risale a una riga di `30-Dati/` con PMID
- coerenza fra `fulltext: si` e presenza del file in `90-Sorgenti/fulltext/`
- `fulltext-mancanti.md` allineato al DB
- nessun PMID duplicato con slug diversi
- `99-Meta/state.sql` allineato a `state.sqlite`
- `50-Metanalisi/`: output generati dal `ma-bracci.csv` e dall'`analisi.R`
  correnti; `ma-rob2.csv` e `grade.csv` validi; `sof.md` e `grade.md` identici
  a quanto rigenera `grade_meta.py --sof`; ogni stima RR/OR/RD/MD con IC citata
  in `40-Sintesi/` coincide con un output e linka `50-Metanalisi/`

**Controllo di completezza (periodico, non a ogni run).** Prendi 2-3 revisioni
sistematiche recenti sul confronto FDI/FCM, estrai i loro riferimenti primari
nella finestra temporale, e verifica che siano tutti nel corpus. Quelli mancanti
indicano un buco nelle query: si corregge `queries.yaml`, non si aggiunge il
paper a mano. Registra l'esito in `99-Meta/log/completezza-<data>.md`.

---

## 9. Regole di condotta per te, Claude

- **Non inventare PMID, DOI, numeri o citazioni.** Mai. Se un dato ti serve e
  non c'è, scrivi che non c'è.
- **Non estrapolare oltre la fonte.** Se uno studio riporta l'incidenza a 35
  giorni, non dedurne l'incidenza a 90.
- **Non fondere dati di studi diversi** in una singola percentuale. Nessuna
  sintesi quantitativa fuori dal protocollo `99-Meta/protocollo-metanalisi.md`
  e fuori da `50-Metanalisi/`: lì i numeri aggregati li producono solo gli
  script (`50-Metanalisi/analisi.R`, `scripts/grade_meta.py`), mai la prosa o
  l'LLM. Il resto del vault fa tabelle di evidenza affiancate; le note di
  `40-Sintesi/` citano le stime aggregate solo linkando `50-Metanalisi/`.
- **Confronti indiretti**: ammessi solo in `40-Sintesi/`, in blocco
  `> [!inferenza]`, con dichiarazione esplicita dell'eterogeneità (popolazione,
  dose, soglia, durata del follow-up).
- **Conflitti di interesse**: nella sintesi, quando più studi convergono e sono
  tutti finanziati dallo stesso produttore, dillo.
- **Se una fonte è irraggiungibile**, non sostituirla con la tua conoscenza
  pregressa. Marca `da-recuperare`.
- **Non modificare `90-Sorgenti/`** se non tramite gli script.
- **Stato in SQLite, non in testa.** Prima di iniziare qualunque stadio, leggi
  lo stato con `python3 scripts/status.py`.
- Questo vault è materiale di lavoro scientifico interno, non produce
  raccomandazioni cliniche. Le note di sintesi non contengono indicazioni
  terapeutiche dirette.

---

## 10. Avvio rapido

```bash
cp .env.example .env && $EDITOR .env      # NCBI_API_KEY, NCBI_EMAIL, UNPAYWALL_EMAIL
pip install -r scripts/requirements.txt
python3 scripts/db.py --init
python3 scripts/pubmed_harvest.py --all --dry-run    # controlla i volumi
python3 scripts/pubmed_harvest.py --all
python3 scripts/status.py
```

Poi, in Claude Code: `/pubmed-harvest`, `/fulltext-fetch`, `/paper-ingest`,
`/vault-lint`.

---

## 11. Variabili d'ambiente

| Variabile | Obbligatoria | Uso |
|---|---|---|
| `NCBI_API_KEY` | consigliata | E-utilities a 10 req/s invece di 3 |
| `NCBI_EMAIL` | sì | richiesto dalle policy NCBI |
| `NCBI_TOOL` | no | default `fdi-fcm-wiki` |
| `UNPAYWALL_EMAIL` | sì per Unpaywall | parametro obbligatorio dell'API |
| `VAULT_ROOT` | no | default: directory di questo file |

Il file `.env` è in `.gitignore`. Non committare chiavi.
