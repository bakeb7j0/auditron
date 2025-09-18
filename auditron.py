#!/usr/bin/env python3
import argparse
import time
from typing import List

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditron - Host auditing tool")
    parser.add_argument("mode", choices=["fresh", "resume"], help="Run mode")
    parser.add_argument(
        "--db", default="auditron.db", help="Path to the SQLite database file"
    )
    args = parser.parse_args()

    if args.mode == "fresh":
        run_mode(args.db, "fresh")
    else:
        run_resume(args.db)


if __name__ == "__main__":
    main()
