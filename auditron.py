#!/usr/bin/env python3
import argparse
import time
from typing import List, Tuple

from strategies.base import AuditContext
from strategies.osinfo import OSInfo
from strategies.processes import Processes
from strategies.routes import Routes
from strategies.rpm_inventory import RpmInventory
from strategies.rpm_verify import RpmVerify
from strategies.sockets import Sockets
from utils import db
from utils.ssh_runner import SSHClient


def run_all_checks(ctx: AuditContext) -> None:
    checks: List[type] = [OSInfo, Processes, Routes, RpmInventory, RpmVerify, Sockets]
    for Check in checks:
        Check().run(ctx)


def run_mode(db_path: str, mode: str) -> None:
    conn = db.connect(db_path)
    db.ensure_schema(conn)
    session_id = db.new_session(conn, mode)

    hosts = db.get_hosts(conn)
    for host in hosts:
        ssh = SSHClient(host)
        ctx = AuditContext(
            host=host, ssh=ssh, db=conn, limits={}, clock=time, session_id=session_id
        )
        run_all_checks(ctx)

    db.finish_session(conn, session_id)


def run_resume(db_path: str) -> None:
    conn = db.connect(db_path)
    db.ensure_schema(conn)
    session_id = db.get_unfinished_session(conn)
    if session_id is None:
        print("No unfinished session found.")
        return

    hosts = db.get_hosts(conn)
    for host in hosts:
        ssh = SSHClient(host)
        ctx = AuditContext(
            host=host, ssh=ssh, db=conn, limits={}, clock=time, session_id=session_id
        )
        run_all_checks(ctx)

    db.finish_session(conn, session_id)


def parse_cli() -> Tuple[str, str]:
    """Support either positional mode or flags (--fresh / --resume)."""
    parser = argparse.ArgumentParser(description="Auditron - Host auditing tool")
    parser.add_argument(
        "--db", default="auditron.db", help="Path to the SQLite database file"
    )
    # Optional flags for mode (backward/forward compatible with CI & humans)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fresh", action="store_true", help="Start a fresh session")
    group.add_argument("--resume", action="store_true", help="Resume last session")
    # Positional (optional) for previous behavior
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["fresh", "resume"],
        help="Run mode (positional) — or use --fresh/--resume",
    )

    args = parser.parse_args()

    # Resolve final mode with conflict checks
    mode = args.mode
    if args.fresh:
        if mode and mode != "fresh":
            parser.error(f"Conflicting mode: gave positional '{mode}' and --fresh")
        mode = "fresh"
    if args.resume:
        if mode and mode != "resume":
            parser.error(f"Conflicting mode: gave positional '{mode}' and --resume")
        mode = "resume"

    if mode is None:
        parser.error(
            "Specify mode: 'fresh' or 'resume' (positional) or use --fresh/--resume"
        )

    return mode, args.db


def main() -> None:
    mode, db_path = parse_cli()
    if mode == "fresh":
        run_mode(db_path, "new")
    else:
        run_resume(db_path)


if __name__ == "__main__":
    main()
