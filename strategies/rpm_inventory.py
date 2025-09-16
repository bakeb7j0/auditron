from .base import AuditCheck, AuditContext
from . import register

@register
class RpmInventory(AuditCheck):
    name = "rpm_inventory"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("rpm")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import start_check, mark_check, record_error
        check_id = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res = ctx.ssh.run("rpm -qa --qf '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\n'")
            if res.rc != 0:
                record_error(ctx.db, check_id, "run", res.err, res.rc)
                mark_check(ctx.db, check_id, "ERROR", "rpm -qa failed")
                return
            # TODO: parse and insert into rpm_packages; host_id available via ctx.host["id"]
            mark_check(ctx.db, check_id, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, check_id, "run", str(e), -1)
            mark_check(ctx.db, check_id, "ERROR", str(e))
