#!/usr/bin/env python3
"""Gestione di 99-Meta/state.sqlite.

Uso:
    python3 scripts/db.py --init        crea o aggiorna lo schema (idempotente)
    python3 scripts/db.py --vacuum      compatta il database
    python3 scripts/db.py --backup      copia datata in 99-Meta/log/
"""
import argparse
import shutil
from datetime import date

from common import DB_PATH, LOG_DIR, connect, init_db

ap = argparse.ArgumentParser(description="Gestione database del vault")
ap.add_argument("--init", action="store_true")
ap.add_argument("--vacuum", action="store_true")
ap.add_argument("--backup", action="store_true")
args = ap.parse_args()

if not any([args.init, args.vacuum, args.backup]):
    ap.error("specifica --init, --vacuum o --backup")

if args.init:
    init_db()
    print(f"Schema inizializzato: {DB_PATH}")

if args.backup:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dest = LOG_DIR / f"state-{date.today():%Y%m%d}.sqlite"
    shutil.copy2(DB_PATH, dest)
    print(f"Backup: {dest}")

if args.vacuum:
    con = connect()
    con.execute("VACUUM")
    con.close()
    print("VACUUM eseguito.")
