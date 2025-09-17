from .base import AuditCheck, AuditContext
from . import register
@register
class OSInfo(AuditCheck):
    name="osinfo"; requires=()
    def probe(self, ctx: AuditContext)->bool: return True
    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        res_os = ctx.ssh.run("if [ -f /etc/os-release ]; then . /etc/os-release; echo \"$NAME|$VERSION_ID|$ID\"; else cat /etc/centos-release; fi")
        res_uname = ctx.ssh.run("uname -srvm")
        if res_os.rc!=0 or res_uname.rc!=0:
            record_error(ctx.db,cid,"run",res_os.err+res_uname.err,res_os.rc or res_uname.rc); mark_check(ctx.db,cid,"ERROR","osinfo failed"); return
        # TODO: insert into os_info
        mark_check(ctx.db, cid, "SUCCESS", None)
