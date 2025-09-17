from utils.parsing import parse_ss_listen

from .base import AuditCheck, AuditContext


class Sockets(AuditCheck):
    name = "sockets"
    requires = ("ss",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("ss") or ctx.ssh.which("netstat")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            ctx.db.execute("DELETE FROM listen_sockets WHERE host_id=?", (ctx.host["id"],))
            use_ss = ctx.ssh.which("ss")
            cmd = "ss -lntu -pH" if use_ss else "netstat -lpn --tcp --udp | tail -n +3"
            res = ctx.ssh.run(cmd)
            if res.rc != 0 and not res.out.strip():
                record_error(ctx.db, cid, "run", res.err, res.rc); mark_check(ctx.db, cid, "ERROR", f"{cmd} failed"); return
            for ln in (l for l in res.out.splitlines() if l.strip()):
                if use_ss:
                    tup = parse_ss_listen(ln)
                    if not tup: continue
                    proto, local, state, pid, process = tup
                else:
                    parts = ln.split()
                    proto = parts[0]; local = parts[3] if len(parts) > 3 else ""
                    state = parts[5] if len(parts) > 5 else ""
                    pid = None; process = None
                ctx.db.execute("INSERT INTO listen_sockets(host_id, proto, local, state, pid, process) VALUES (?,?,?,?,?,?)",
                               (ctx.host["id"], proto, local, state, pid, process))
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
