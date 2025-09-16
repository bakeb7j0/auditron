from .base import AuditCheck, AuditContext
from . import register

@register
class Sockets(AuditCheck):
    name = "sockets"
    requires = ("ss",)

    def probe(self, ctx: AuditContext) -> bool:
        if ctx.ssh.which("ss"):
            return True
        return ctx.ssh.which("netstat")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import start_check, mark_check, record_error
        check_id = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            cmd = "ss -lntu" if ctx.ssh.which("ss") else "netstat -lpn --tcp --udp"
            res = ctx.ssh.run(cmd)
            if res.rc != 0:
                record_error(ctx.db, check_id, "run", res.err, res.rc)
                mark_check(ctx.db, check_id, "ERROR", f"{cmd} failed")
                return
            # TODO: parse and persist into listen_sockets
            mark_check(ctx.db, check_id, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, check_id, "run", str(e), -1)
            mark_check(ctx.db, check_id, "ERROR", str(e))
