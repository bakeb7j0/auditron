from .base import AuditCheck, AuditContext
from . import register
from utils.parsing import parse_rpm_verify
@register
class RpmVerify(AuditCheck):
    name="rpm_verify"; requires=("rpm",)
    def probe(self, ctx: AuditContext)->bool: return ctx.ssh.which("rpm")
    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        res = ctx.ssh.run("rpm -Va")
        if res.rc!=0 and not res.out.strip(): record_error(ctx.db,cid,"run",res.err,res.rc); mark_check(ctx.db,cid,"ERROR","rpm -Va failed"); return
        _rows = parse_rpm_verify(res.out)
        # TODO: persist verify flags and optionally file snapshots
        mark_check(ctx.db, cid, "SUCCESS", None)
