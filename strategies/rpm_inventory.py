from .base import AuditCheck, AuditContext
from . import register
@register
class RpmInventory(AuditCheck):
    name="rpm_inventory"; requires=("rpm",)
    def probe(self, ctx: AuditContext)->bool: return ctx.ssh.which("rpm")
    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        res = ctx.ssh.run("rpm -qa --qf '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\\n'")
        if res.rc!=0: record_error(ctx.db, cid,"run",res.err,res.rc); mark_check(ctx.db,cid,"ERROR","rpm -qa failed"); return
        # TODO: insert into rpm_packages
        mark_check(ctx.db, cid, "SUCCESS", None)
