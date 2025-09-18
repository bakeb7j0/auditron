from utils.db import mark_check, record_error, start_check
from utils.parsing import parse_ss_listen

from .base import AuditCheck, AuditContext


class Sockets(AuditCheck):
    name = "sockets"
    requires: tuple[str, ...] = ()

    def probe(self, ctx: AuditContext) -> bool:
        return bool(ctx.ssh.which("ss") or ctx.ssh.which("netstat"))

    def run(self, ctx: AuditContext) -> None:
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            use_ss = bool(ctx.ssh.which("ss"))
            cmd = (
                "ss -lptnH" if use_ss else "netstat -lptn --numeric-hosts | tail -n +3"
            )
            res = ctx.ssh.run(cmd)
            if res.rc != 0 and not res.out.strip():
                record_error(ctx.db, cid, "run", res.err, res.rc)
                mark_check(ctx.db, cid, "ERROR", f"{cmd} failed")
                return

            for ln in (ln for ln in res.out.splitlines() if ln.strip()):
                if use_ss:
                    parsed = parse_ss_listen(ln)
                    if parsed is None:
                        continue
                    proto, local, state, pid, process = parsed
                else:
                    parts = ln.split()
                    proto = parts[0] if parts else ""
                    local = parts[3] if len(parts) > 3 else ""
                    state = parts[5] if len(parts) > 5 else ""
                    pid = None
                    process = None

                ctx.db.execute(
                    "INSERT INTO listen_sockets(host_id, proto, local, state, pid, process) VALUES (?,?,?,?,?,?)",
                    (ctx.host["id"], proto, local, state, pid, process),
                )

            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:  # noqa: BLE001
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
