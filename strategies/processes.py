from .base import AuditCheck, AuditContext
from . import register
@register
class Processes(AuditCheck):
    name="processes"; requires=("ps",)
    def probe(self, ctx: AuditContext)->bool: return ctx.ssh.which("ps")
    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        res = ctx.ssh.run("ps -eo pid,ppid,user,lstart,etime,cmd")
        if res.rc!=0: record_error(ctx.db,cid,"run",res.err,res.rc); mark_check(ctx.db,cid,"ERROR","ps failed"); return
        # TODO: persist processes and optional open files
        mark_check(ctx.db, cid, "SUCCESS", None)
