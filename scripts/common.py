"""Utilità condivise: configurazione, env, DB, logging, rate limiting."""
from __future__ import annotations

import os
import re
import sqlite3
import sys
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", Path(__file__).resolve().parent.parent))
META = VAULT_ROOT / "99-Meta"
DB_PATH = META / "state.sqlite"
QUERIES_PATH = META / "queries.yaml"
LOG_DIR = META / "log"

DIR_ABSTRACT = VAULT_ROOT / "90-Sorgenti" / "abstract"
DIR_FULLTEXT = VAULT_ROOT / "90-Sorgenti" / "fulltext"
DIR_PDF = VAULT_ROOT / "90-Sorgenti" / "pdf"
DIR_INBOX = VAULT_ROOT / "90-Sorgenti" / "inbox-pdf"
DIR_PAPER = VAULT_ROOT / "20-Paper"
DIR_DATI = VAULT_ROOT / "30-Dati"


# --------------------------------------------------------------------------- env
def _load_dotenv() -> None:
    env_file = VAULT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "").strip()
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "").strip()
NCBI_TOOL = os.environ.get("NCBI_TOOL", "fdi-fcm-wiki").strip()
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "").strip()

USER_AGENT = f"{NCBI_TOOL}/1.0 (mailto:{NCBI_EMAIL or UNPAYWALL_EMAIL or 'unset'})"


def require_env(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n, "").strip()]
    if missing:
        sys.exit(
            f"ERRORE: variabili d'ambiente mancanti: {', '.join(missing)}.\n"
            f"Copia .env.example in .env e compilalo."
        )


# ------------------------------------------------------------------ rate limiting
class RateLimiter:
    """Finestra scorrevole semplice. NCBI: 3 req/s senza API key, 10 con."""

    def __init__(self, per_second: float):
        self.interval = 1.0 / per_second
        self._last = 0.0

    def wait(self) -> None:
        delta = time.monotonic() - self._last
        if delta < self.interval:
            time.sleep(self.interval - delta)
        self._last = time.monotonic()


ncbi_limiter = RateLimiter(9.0 if NCBI_API_KEY else 2.5)


# ------------------------------------------------------------------------- config
def load_queries() -> dict:
    with QUERIES_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def query_spec(name: str, cfg: dict) -> dict:
    """Specifica di una query: prima fra quelle del wiki (`query`), poi fra
    quelle della meta-analisi (`query_meta`), che --all non esegue."""
    if name in cfg["query"]:
        return cfg["query"][name]
    return (cfg.get("query_meta") or {})[name]


def senza_finestra(spec: dict) -> bool:
    return str(spec.get("finestra", "mobile")).strip().lower() == "nessuna"


# Qualunque limite di data PubMed: nel term si scrive [dp], [pdat]…; nella
# querytranslation PubMed lo riscrive come [Date - Publication], [Date - Entry]…
LIMITE_DATA_RE = re.compile(
    r"\[(dp|pdat|edat|crdt|mhda|lr|dcom|da|epdat|ppdat"
    r"|publication date|entrez date|date\s*-\s*[^\]]+)\]"
    r"|\b(mindate|maxdate|reldate)\b",
    re.IGNORECASE,
)


def build_term(name: str, cfg: dict) -> str:
    """Interpola i blocchi, aggiunge finestra temporale ed esclusioni.

    Una query con `finestra: nessuna` non riceve alcun limite di data
    (protocollo di meta-analisi, §7.1). Una query con `exclude_pubtypes`
    propri usa quelli al posto della lista globale."""
    spec = query_spec(name, cfg)
    term = spec["term"]
    for _ in range(4):  # i blocchi non si annidano oltre un livello, 4 è abbondante
        new = term.format(**{k: v.strip() for k, v in cfg["blocchi"].items()})
        if new == term:
            break
        term = new
    term = " ".join(term.split())

    if senza_finestra(spec):
        if LIMITE_DATA_RE.search(term):
            raise ValueError(f"{name}: dichiarata senza finestra ma il term contiene "
                             "un limite di data")
    else:
        anni = int(cfg["finestra"]["anni_indietro"])
        oggi = date.today()
        try:
            inizio = oggi.replace(year=oggi.year - anni)
        except ValueError:  # 29 febbraio
            inizio = oggi.replace(year=oggi.year - anni, day=28)
        term += f' AND ("{inizio:%Y/%m/%d}"[dp] : "3000"[dp])'

    if name not in (cfg.get("no_exclude") or []):
        pubtypes = spec.get("exclude_pubtypes", cfg["exclude_pubtypes"])
        if pubtypes:
            excl = " OR ".join(f'"{pt}"[pt]' for pt in pubtypes)
            term += f" NOT ({excl})"
    return term


# ----------------------------------------------------------------------------- DB
SCHEMA = """
CREATE TABLE IF NOT EXISTS record (
    pmid                  TEXT PRIMARY KEY,
    doi                   TEXT,
    pmcid                 TEXT,
    titolo                TEXT,
    autori                TEXT,
    anno                  INTEGER,
    rivista               TEXT,
    pubtypes              TEXT,
    lingua                TEXT,
    abstract              TEXT,
    stato_screening       TEXT,
    motivo_screening      TEXT,
    design                TEXT,
    fulltext              TEXT DEFAULT 'no',
    fonte_fulltext        TEXT DEFAULT 'nd',
    fulltext_path         TEXT,
    fulltext_motivo       TEXT,
    fulltext_url          TEXT,
    tentativi_fulltext    INTEGER DEFAULT 0,
    stato_ingest          TEXT DEFAULT 'non-iniziato',
    nota_path             TEXT,
    primo_harvest         TEXT,
    ultimo_aggiornamento  TEXT,
    corpus                TEXT NOT NULL DEFAULT 'wiki'
                          CHECK (corpus IN ('wiki', 'meta', 'wiki+meta'))
);
CREATE TABLE IF NOT EXISTS record_query (
    pmid  TEXT NOT NULL,
    query TEXT NOT NULL,
    PRIMARY KEY (pmid, query)
);
CREATE TABLE IF NOT EXISTS run_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT,
    script    TEXT,
    azione    TEXT,
    esito     TEXT,
    dettaglio TEXT
);
CREATE INDEX IF NOT EXISTS idx_screening ON record(stato_screening);
CREATE INDEX IF NOT EXISTS idx_ingest    ON record(stato_ingest);
CREATE INDEX IF NOT EXISTS idx_fulltext  ON record(fulltext);

-- Meta-analisi (protocollo §5): l'unità di analisi è il trial, non il PMID.
-- Un articolo può riportare più trial (PHOSPHARE-IDA A e B, PMID 32016310) e un
-- trial ha più articoli (primaria, post-hoc): per questo è una tabella di
-- collegamento e non una colonna di record.
CREATE TABLE IF NOT EXISTS trial (
    trial_id       TEXT PRIMARY KEY,   -- NCT…, EudraCT…, ISRCTN…, o TRIAL-<pmid primaria>
    acronimo       TEXT,
    altri_registri TEXT,               -- altri identificativi dello stesso trial
    note           TEXT
);
CREATE TABLE IF NOT EXISTS trial_pubblicazione (
    trial_id TEXT NOT NULL REFERENCES trial(trial_id),
    pmid     TEXT NOT NULL REFERENCES record(pmid),
    ruolo    TEXT NOT NULL CHECK (ruolo IN ('primaria', 'secondaria', 'registro')),
    note     TEXT,
    PRIMARY KEY (trial_id, pmid)
);
"""

# Colonne della meta-analisi su record (protocollo §8): due fasi PRISMA,
# titolo/abstract e fulltext, ciascuna con motivo. Aggiunte da init_db() ai DB
# esistenti; i CHECK impediscono decisioni meta su record del solo wiki e una
# decisione sul fulltext senza passaggio dalla fase precedente.
COLONNE_META = [
    ("stato_screening_meta", "TEXT CHECK (stato_screening_meta IS NULL OR "
     "(stato_screening_meta IN ('incluso','escluso','dubbio') AND corpus != 'wiki'))"),
    ("motivo_screening_meta", "TEXT"),
    # 'in-attesa' = «awaiting classification» del PRISMA 2020: protocolli e
    # registrazioni senza risultati (criteri-screening-meta.md).
    ("stato_eleggibilita_meta", "TEXT CHECK (stato_eleggibilita_meta IS NULL OR "
     "(stato_eleggibilita_meta IN ('incluso','escluso','dubbio','in-attesa') "
     "AND COALESCE(stato_screening_meta, '') IN ('incluso','dubbio')))"),
    ("motivo_eleggibilita_meta", "TEXT"),
]

# Corpus di appartenenza (protocollo di meta-analisi, §8). Il wiki ha la finestra
# di 5 anni, la meta-analisi no: un record intercettato solo da query_meta è
# 'meta' e il wiki non lo vede. Ogni SELECT sull'insieme dei record del wiki
# deve filtrare con IN_WIKI; gli UPDATE per singolo PMID non ne hanno bisogno.
IN_WIKI = "corpus IN ('wiki','wiki+meta')"
IN_META = "corpus IN ('meta','wiki+meta')"


def corpus_query(name: str, cfg: dict) -> str:
    return "meta" if name in (cfg.get("query_meta") or {}) else "wiki"


def unisci_corpus(attuale: str | None, nuovo: str) -> str:
    insieme = set((attuale or "").split("+")) | {nuovo}
    insieme.discard("")
    return "wiki+meta" if insieme == {"wiki", "meta"} else insieme.pop()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    con = connect()
    con.executescript(SCHEMA)
    colonne = {r["name"] for r in con.execute("PRAGMA table_info(record)")}
    if "corpus" not in colonne:
        # Migrazione 2026-09-29: i record esistenti vengono tutti da Q1-Q9.
        con.execute("ALTER TABLE record ADD COLUMN corpus TEXT NOT NULL DEFAULT 'wiki' "
                    "CHECK (corpus IN ('wiki', 'meta', 'wiki+meta'))")
    con.execute("CREATE INDEX IF NOT EXISTS idx_corpus ON record(corpus)")
    sql_record = con.execute(
        "SELECT sql FROM sqlite_master WHERE name='record'").fetchone()["sql"]
    if "stato_eleggibilita_meta" in colonne and "'in-attesa'" not in sql_record:
        # Migrazione 2026-09-29: il CHECK non si modifica in SQLite; la colonna
        # si ricrea, ma solo se è ancora vuota.
        pieni = con.execute("SELECT COUNT(*) FROM record "
                            "WHERE stato_eleggibilita_meta IS NOT NULL").fetchone()[0]
        if pieni:
            raise RuntimeError("stato_eleggibilita_meta ha già valori: migrazione "
                               "manuale necessaria")
        con.execute("ALTER TABLE record DROP COLUMN stato_eleggibilita_meta")
        colonne.discard("stato_eleggibilita_meta")
    sql_tp = con.execute(
        "SELECT sql FROM sqlite_master WHERE name='trial_pubblicazione'").fetchone()["sql"]
    if "'registro'" not in sql_tp:
        # Migrazione 2026-09-29: ruolo 'registro' per le registrazioni dei trial
        # (fonti_meta.py). Si ricrea la tabella, ma solo se è ancora vuota.
        if con.execute("SELECT COUNT(*) FROM trial_pubblicazione").fetchone()[0]:
            raise RuntimeError("trial_pubblicazione non è vuota: migrazione manuale")
        con.execute("DROP TABLE trial_pubblicazione")
        con.executescript(SCHEMA)
    for nome, tipo in COLONNE_META:
        if nome not in colonne:
            con.execute(f"ALTER TABLE record ADD COLUMN {nome} {tipo}")
    con.commit()
    con.close()


def log_run(script: str, azione: str, esito: str, dettaglio: str = "") -> None:
    con = connect()
    con.execute(
        "INSERT INTO run_log (ts, script, azione, esito, dettaglio) VALUES (?,?,?,?,?)",
        (now_iso(), script, azione, esito, dettaglio[:4000]),
    )
    con.commit()
    con.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# -------------------------------------------------------------------------- testo
def slugify(text: str, max_words: int = 5) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    stop = {
        "a", "an", "the", "of", "in", "on", "for", "and", "or", "with", "to",
        "is", "are", "at", "by", "from", "as", "vs", "versus",
    }
    words = [w for w in text.split() if w and w not in stop]
    return "-".join(words[:max_words]) or "senza-titolo"


def paper_filename(pmid: str, titolo: str) -> str:
    return f"{pmid}-{slugify(titolo)}.md"
