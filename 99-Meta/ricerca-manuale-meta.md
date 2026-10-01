---
tipo: meta
descrizione: Stringhe e istruzioni per le ricerche della meta-analisi che si
  eseguono a mano, perché le fonti vietano o non offrono l'accesso automatico
  (protocollo §7). Le esegue l'utente nel proprio Firefox.
---

# Ricerche manuali — meta-analisi FDI vs FCM

Regole valide per tutte e tre le fonti (protocollo §7.1):

- **nessun limite di data**, di lingua o di tipo di pubblicazione;
- **nessun filtro di disegno** (niente «RCT only»): lo screening seleziona;
- **non escludere gli abstract congressuali** (vedi il log della ricerca del
  2026-09-29: sono il buco principale delle fonti gratuite);
- annotare **data, ora e numero di risultati** mostrato dalla fonte;
- esportare **tutti** i risultati, con abstract, nel formato indicato;
- salvare il file in `99-Meta/log/export-ricerca/` con il nome indicato.
  Poi dimmi che c'è: l'importazione la faccio io.

Se la fonte segnala un errore di sintassi o un termine non riconosciuto, non
correggerlo a occhio: copiami il messaggio. Ogni modifica alla stringa va
registrata.

## 1. Embase (embase.com, accesso istituzionale)

Ricerca avanzata (*Advanced*), campo unico. Disattivare le opzioni di mappatura
automatica aggiuntive se la stringa viene riscritta.

```
('ferric derisomaltose'/exp OR 'iron isomaltoside'/exp OR 'ferric derisomaltose':ti,ab,tn OR 'iron isomaltoside':ti,ab,tn OR 'isomaltoside 1000':ti,ab,tn OR monofer:ti,ab,tn OR monoferric:ti,ab,tn OR diafer:ti,ab,tn)
AND
('ferric carboxymaltose'/exp OR 'ferric carboxymaltose':ti,ab,tn OR carboxymaltose:ti,ab,tn OR ferinject:ti,ab,tn OR injectafer:ti,ab,tn)
```

- Se `'iron isomaltoside'/exp` o `'ferric derisomaltose'/exp` non esistono come
  termine Emtree, Embase lo dice: in quel caso copiami il messaggio. Il nome
  Emtree corrente va verificato nella scheda del termine.
- Nessun limite (*Limits*): lasciare inclusi *Conference Abstract*, *Conference
  Review*, *Article in Press*, e le fonti MEDLINE e non-MEDLINE.
- Export: *Export* → formato **RIS** → selezionare **tutti i record** e i campi
  *Citation, Abstract, Index terms* (se disponibile, anche *PubMed ID* e *DOI*).
- File: `embase-AAAA-MM-GG.ris`.

## 2. Cochrane CENTRAL (cochranelibrary.com)

*Advanced search* → *Search manager*, una riga per volta:

```
#1 ("ferric derisomaltose" OR "iron isomaltoside" OR "isomaltoside 1000" OR Monofer OR Monoferric OR Diafer):ti,ab,kw
#2 ("ferric carboxymaltose" OR carboxymaltose OR Ferinject OR Injectafer):ti,ab,kw
#3 #1 AND #2
```

- Nessun limite di data (*Search limits* vuoti).
- Aprire #3 → scheda **Trials** (non Cochrane Reviews) → annotare il numero.
- Export: selezionare tutti → *Export selected citation(s)* → formato **RIS**
  con abstract.
- File: `central-AAAA-MM-GG.ris`.

## 3. WHO ICTRP (trialsearch.who.int)

*Advanced search*:

- campo **Intervention**:
  `(isomaltoside OR derisomaltose OR Monofer OR Monoferric OR Diafer) AND (carboxymaltose OR Ferinject OR Injectafer)`
- *Recruitment status*: **ALL**; nessun altro filtro.
- Spuntare, se presente, *Search for clinical trials in children* **no**
  (lasciare la ricerca su tutte le età: l'età si valuta nello screening).
- Export: *Export all results to XML*.
- File: `ictrp-AAAA-MM-GG.xml`.

Se la ricerca avanzata non accetta la stringa booleana, fare due ricerche
(`isomaltoside OR derisomaltose OR Monofer` e `carboxymaltose OR Ferinject`),
esportarle entrambe (`ictrp-fdi-…xml`, `ictrp-fcm-…xml`): l'intersezione la
calcola lo script, come per CTIS.

## Dopo le tre ricerche

Scrivimi, per ciascuna fonte: data, ora, numero di risultati mostrato, e se
hai dovuto cambiare qualcosa nella stringa. Io importo i file con
`scripts/export_meta.py` (prima `--dry-run`), deduplico contro i record già nel
DB e lancio il doppio screening di fase 1 su tutti i record nuovi insieme.

L'importatore riconosce come duplicati certi i record con PMID, DOI,
identificativo della fonte o numero di registro già nel DB. Quelli che
coincidono solo per titolo (tipicamente un abstract congressuale e l'articolo
con lo stesso titolo) li elenca e si ferma: decidi tu se sono duplicati o
record nuovi.
