from .base import AuditCheck, AuditContext
from . import register

@register
class Processes(AuditCheck):
    name = "processes"
    requires = ("ps",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("ps")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import start_check, mark_check, record_error
        check_id = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res = ctx.ssh.run("ps -eo pid,ppid,user,lstart,etime,cmd")
            if res.rc != 0:
                record_error(ctx.db, check_id, "run", res.err, res.rc)
                mark_check(ctx.db, check_id, "ERROR", "ps failed")
                return
            # TODO: parse rows into processes; consider follow-up lsof per pid
            mark_check(ctx.db, check_id, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, check_id, "run", str(e), -1)
            mark_check(ctx.db, check_id, "ERROR", str(e))
