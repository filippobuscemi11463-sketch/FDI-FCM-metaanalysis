---
tipo: log
descrizione: Esiti dei giri di fact-checking (subagente fact-checker) sul manoscritto della
  revisione sistematica FDI vs FCM, 2026-09-29. Trascritti dai rapporti degli agenti; le
  correzioni conseguenti sono nei commit indicati. Serve al lavoro di metodo.
---

# Fact-checking del manoscritto della revisione sistematica — 2026-09-29

Ogni giro è composto da due verifiche indipendenti, in sola lettura, eseguite dal subagente
`fact-checker`: la parte A copre abstract, metodi, PRISMA e dichiarazioni; la parte B risultati,
tabelle e discussione. Le fonti ammesse erano i file del vault (protocollo, guide, log, CSV,
output degli script, fulltext). Le categorie sono quelle usate dagli agenti.

## Conteggi per giro

| giro | parte | errori | imprecisioni | suggerimenti | numeri verificati | versione verificata | correzioni |
|---|---|---|---|---|---|---|---|
| 1 | A | 8 | 14 | 4 | | cda86c2 | b3cadf6, 094cde9 |
| 1 | B | 5 | 9 | 5 | 60 | cda86c2 | b3cadf6, 094cde9 |
| 2 | A | 2 | 9 | 9 | | 094cde9 | f5bae06 |
| 2 | B | 1 | 6 | 5 | 85 | 094cde9 | f5bae06 |
| 3 | mirato | 0 | 5 | 0 | 70 | f5bae06 | 145bc29 |

Nel giro 3 l'agente ha verificato i 10 punti corretti nel giro 2: 9 risolti, 1 risolto in parte.
Ha poi segnalato 5 problemi nuovi, 2 di gravità media e 3 bassa, senza classificarli come «errori»: per questo il giro 3 ha 0 errori e 5 imprecisioni. Uno dei due problemi di gravità media ha cambiato i dati.

Nei giri 1 e 2 tutti i conteggi PRISMA e tutti i valori numerici controllati coincidevano con
gli output degli script. Gli errori riguardavano la descrizione del metodo e le affermazioni
qualitative.

## Problemi che hanno cambiato l'analisi, i dati o la loro dichiarazione

| giro | problema | conseguenza | tipo |
|---|---|---|---|
| 1 | Lo script non aggregava gli esiti con meno di 2 trial con eventi; il protocollo chiedeva 2 trial con dati | Regola corretta; RD come misura principale per S8b (deviazione §15) | analisi |
| 1 | Sottogruppi prespecificati non eseguiti | Sottogruppi per schema di dose aggiunti allo script | analisi |
| 1 | Confronto registrati/pubblicati prespecificato non eseguito | Confronto descrittivo aggiunto | analisi |
| 1 | Analisi di sensibilità sul nadir dichiarata ma non eseguita | Dichiarata come non eseguita | dichiarazione |
| 2 | ExplorIRON-CKD in S1 con soglia 0,30 mmol/L, contro la regola della soglia per difetto | Trial tolto da S1 | dati |
| 3 | Riga di ExplorIRON-CKD per P1 in finestra estesa non usata senza motivo scritto | Riga usata; P1 estesa aggregata come RD | dati |

## Affermazioni false del testo generato dal modello, individuate dal fact-checker

Le righe con giro «metodo» sono state aggiunte il 2026-10-01: le affermazioni sono state trovate dai fact-check
del lavoro di metodo, non da uno dei tre giri sul manoscritto della revisione, che le conteneva già (145bc29). La nota «Consenso 2026-09-29 (utente)» nei file
`99-Meta/log/rob2/*-consenso.csv` non indica l'approvazione dei giudizi concordi: l'utente ha deciso solo le discordanze.

| giro | affermazione | realtà documentata | oggetto |
|---|---|---|---|
| 1 | Gli agenti non hanno preso decisioni finali; gli autori hanno verificato ogni decisione | Le esclusioni concordi in fase 1 sono state registrate senza revisione dell'utente | procedura |
| 1 | Tutti i trial degli esiti sul fosfato sono finanziati dal produttore di FDI | Falso per S1 (RD) e S2 | contenuto |
| 1 | I giudizi ad alto rischio nascono tutti dal cumulo di domini | Vero solo per un trial; l'altro è alto per il dominio D1 | contenuto |
| 1 | Aggiudicazione attribuita alle reazioni del trial sbagliato | L'aggiudicazione esterna era in RAPIDIRON, non nei PHOSPHARE-IDA | contenuto |
| 1 | Crossref aggiunto «prima della selezione» | Aggiunto dopo lo screening dei 147 record PubMed | procedura |
| 1 | Ricerche in Embase, CENTRAL e ICTRP presentate come eseguite nell'abstract | Non eseguite | procedura |
| 2 | Agenti «sempre in due passaggi indipendenti» | L'eleggibilità è stata preparata da un solo passaggio e approvata in blocco | procedura |
| 2 | Tabella delle deviazioni «completa» | Mancava il confronto registrati/pubblicati (e altre voci) | procedura |
| 2 | La finestra estesa di P1 inclusa fra gli esiti a certezza molto bassa | Certezza bassa | contenuto |
| 3 | Farmaci di RAPIDIRON «forniti dai produttori» | Acquistati da un distributore commerciale | contenuto |
| metodo | Le discordanze GRADE fra i due passaggi sono state decise dall'autore (Metodi della revisione; lavoro di metodo) | Risolte dall'agente nel consenso del 2026-09-29; decise dall'utente solo il 2026-10-01, confermando il consenso (deviazione §15) | procedura |
| metodo | Un autore ha approvato ogni giudizio di consenso RoB 2 e GRADE; tutte le decisioni finali di RoB 2 e GRADE prese da un autore (Metodi e dichiarazioni della revisione, testo OSF) | L'utente ha deciso solo le discordanze; i giudizi concordi sono stati accettati senza revisione (dichiarazione dell'utente, 2026-10-01) | procedura |
