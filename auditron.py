#!/usr/bin/env python3
import argparse
import os
import sys
import time

from strategies import REGISTRY
from strategies.base import AuditContext
from utils import db as dbutil
from utils.ssh_runner import SSHClient

try:
    from rich.progress import Progress
    use_rich = True
except Exception:
    use_rich = False

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "auditron.db")

def resolve_limits(conn, host_id: int) -> dict:
    cur = conn.execute("SELECT max_snapshot_bytes, gzip_snapshots, command_timeout_sec FROM global_defaults WHERE id=1")
    g = cur.fetchone() or (524288, 1, 60)
    cur = conn.execute("SELECT max_snapshot_bytes, gzip_snapshots, command_timeout_sec FROM host_overrides WHERE host_id=?", (host_id,))
    h = cur.fetchone()
    msb, gz, to = g
    if h:
        msb = h[0] if h[0] is not None else msb
        gz  = h[1] if h[1] is not None else gz
        to  = h[2] if h[2] is not None else to
    return {"max_snapshot_bytes": int(msb), "gzip_snapshots": int(gz), "command_timeout_sec": int(to)}

def main():
    ap = argparse.ArgumentParser(description="Auditron Orchestrator (serial v1)")
    ap.add_argument("--resume", action="store_true", help="Resume last incomplete session if present")
    ap.add_argument("--host", help="Limit to a single host (hostname or IP)")
    ap.add_argument("--skip", help="Comma-separated check names to skip")
    ap.add_argument("--timeout", type=int, help="Override per-command timeout seconds")
    args = ap.parse_args()

    conn = dbutil.connect(DB_PATH); dbutil.ensure_schema(conn)
    session_id = dbutil.get_unfinished_session(conn) if args.resume else None
    if not session_id: session_id = dbutil.new_session(conn, "resume" if args.resume else "new")

    hosts = dbutil.get_hosts(conn)
    if args.host:
        hosts = [h for h in hosts if h["hostname"] == args.host or (h.get("ip") and h["ip"] == args.host)]
        if not hosts:
            print(f"No matching host for {args.host}"); sys.exit(1)

    skip_set = set([(args.skip or "").split(",")][0]) if args.skip else set()

    def run_host(h):
        limits = resolve_limits(conn, h["id"])
        if args.timeout: limits["command_timeout_sec"] = args.timeout
        ssh = SSHClient(h, timeout=limits["command_timeout_sec"])
        ctx = AuditContext(host=h, ssh=ssh, db=conn, limits=limits, clock=time)
        ctx.session_id = session_id
        for strat_cls in REGISTRY:
            strat = strat_cls()
            if strat.name in skip_set:
                rid = dbutil.start_check(conn, session_id, h["id"], strat.name)
                dbutil.mark_check(conn, rid, "SKIP", "skipped via CLI"); continue
            if hasattr(strat, "probe") and not strat.probe(ctx):
                rid = dbutil.start_check(conn, session_id, h["id"], strat.name)
                dbutil.mark_check(conn, rid, "SKIP", "prereq not met"); continue
            strat.run(ctx)

    if use_rich:
        with Progress() as progress:
            t = progress.add_task("[cyan]Auditing hosts...", total=len(hosts))
            for h in hosts:
                progress.console.print(f"[bold]Host:[/bold] {h['hostname'] or h.get('ip','?')}")
                run_host(h); progress.advance(t)
    else:
        for i,h in enumerate(hosts,1):
            print(f"[{i}/{len(hosts)}] Host: {h['hostname'] or h.get('ip','?')}"); run_host(h)

    dbutil.finish_session(conn, session_id); print("Audit complete. Session:", session_id)

if __name__ == "__main__":
    main()
