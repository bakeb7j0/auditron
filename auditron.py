#!/usr/bin/env python3
import argparse, os, sys, time
from utils import db as dbutil
from utils.ssh_runner import SSHClient
from strategies import REGISTRY
from strategies.base import AuditContext
try:
    from rich.progress import Progress
    use_rich = True
except Exception:
    use_rich = False

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "auditron.db")

def main():
    ap = argparse.ArgumentParser(description="Auditron Orchestrator (serial v1)")
    ap.add_argument("--resume", action="store_true", help="Resume last incomplete session if present")
    ap.add_argument("--host", help="Limit to a single host (hostname or IP)")
    ap.add_argument("--skip", help="Comma-separated check names to skip")
    ap.add_argument("--timeout", type=int, default=60, help="Per-command timeout seconds")
    args = ap.parse_args()

    conn = dbutil.connect(DB_PATH)
    dbutil.ensure_schema(conn)

    if args.resume:
        session_id = dbutil.get_unfinished_session(conn) or dbutil.new_session(conn, "resume")
    else:
        unfinished = dbutil.get_unfinished_session(conn)
        session_id = unfinished if unfinished else dbutil.new_session(conn, "new")

    hosts = dbutil.get_hosts(conn)
    if args.host:
        hosts = [h for h in hosts if h["hostname"] == args.host or h["ip"] == args.host]
        if not hosts:
            print(f"No matching host found for {args.host}")
            sys.exit(1)

    skip_set = set((args.skip or "").split(",")) if args.skip else set()

    def run_host(h):
        ssh = SSHClient(h, timeout=args.timeout)
        ctx = AuditContext(host=h, ssh=ssh, db=conn, limits={}, clock=time)
        # attach session_id to context (simple injection)
        ctx.session_id = session_id
        for strat_cls in REGISTRY:
            strat = strat_cls()
            if strat.name in skip_set:
                # create a check run row and mark SKIP for visibility
                rid = dbutil.start_check(conn, session_id, h["id"], strat.name)
                dbutil.mark_check(conn, rid, "SKIP", "skipped via CLI")
                continue
            if hasattr(strat, "probe") and not strat.probe(ctx):
                rid = dbutil.start_check(conn, session_id, h["id"], strat.name)
                dbutil.mark_check(conn, rid, "SKIP", "prereq not met")
                continue
            strat.run(ctx)

    if use_rich:
        with Progress() as progress:
            task = progress.add_task("[cyan]Auditing hosts...", total=len(hosts))
            for h in hosts:
                progress.console.print(f"[bold]Host:[/bold] {h['hostname'] or h['ip']}")
                run_host(h)
                progress.advance(task)
    else:
        for i, h in enumerate(hosts, 1):
            print(f"[{i}/{len(hosts)}] Host: {h['hostname'] or h['ip']}")
            run_host(h)

    dbutil.finish_session(conn, session_id)
    print("Audit complete. Session:", session_id)

if __name__ == "__main__":
    main()
