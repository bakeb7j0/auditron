from .base import AuditCheck, AuditContext
from . import register
@register
class Sockets(AuditCheck):
    name="sockets"; requires=("ss",)
    def probe(self, ctx: AuditContext)->bool:
        return ctx.ssh.which("ss") or ctx.ssh.which("netstat")
    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        cmd = "ss -lntu" if ctx.ssh.which("ss") else "netstat -lpn --tcp --udp"
        res = ctx.ssh.run(cmd)
        if res.rc!=0: record_error(ctx.db,cid,"run",res.err,res.rc); mark_check(ctx.db,cid,"ERROR",f"{cmd} failed"); return
        # TODO: persist listen_sockets
        mark_check(ctx.db, cid, "SUCCESS", None)
