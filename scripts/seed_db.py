#!/usr/bin/env python3
import argparse, os, sqlite3, time, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "auditron.db"
SCHEMA = ROOT / "docs" / "schema.sql"

def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON;")
    with open(SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn

def init_defaults(conn):
    cur = conn.execute("SELECT 1 FROM global_defaults WHERE id=1")
    if not cur.fetchone():
        conn.execute("INSERT INTO global_defaults(id) VALUES (1)")
        conn.commit()
        print("Inserted global default flags (all ON).")
    else:
        print("Global defaults already present.")

def add_host(conn, name, ip, user, key, port, sudo):
    conn.execute(
        "INSERT INTO hosts(hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) VALUES (?,?,?,?,?,?)",
        (name, ip, user, key, port, 1 if sudo else 0)
    )
    conn.commit()
    print(f"Added host: {name} ({ip})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-defaults", action="store_true", help="Insert global defaults row if missing")
    ap.add_argument("--add-host", metavar="NAME", help="Hostname to add")
    ap.add_argument("--ip", help="IP address")
    ap.add_argument("--user", default="root", help="SSH username")
    ap.add_argument("--key", help="SSH private key path")
    ap.add_argument("--port", type=int, default=22, help="SSH port")
    ap.add_argument("--sudo", action="store_true", help="Use sudo on target")
    args = ap.parse_args()

    conn = ensure_db()

    if args.init_defaults:
        init_defaults(conn)

    if args.add_host:
        if not args.ip:
            print("--ip is required with --add-host")
            sys.exit(1)
        add_host(conn, args.add_host, args.ip, args.user, args.key, args.port, args.sudo)

if __name__ == "__main__":
    main()
