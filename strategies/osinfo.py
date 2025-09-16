from .base import AuditCheck, AuditContext
from . import register

@register
class OSInfo(AuditCheck):
    name = "osinfo"
    requires = ()

    def probe(self, ctx: AuditContext) -> bool:
        return True

    def run(self, ctx: AuditContext) -> None:
        from utils.db import start_check, mark_check, record_error
        check_id = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res_os = ctx.ssh.run("if [ -f /etc/os-release ]; then . /etc/os-release; echo $NAME|$VERSION_ID; else cat /etc/centos-release; fi")
            res_uname = ctx.ssh.run("uname -srvm")
            if res_os.rc != 0 or res_uname.rc != 0:
                record_error(ctx.db, check_id, "run", res_os.err + res_uname.err, res_os.rc or res_uname.rc)
                mark_check(ctx.db, check_id, "ERROR", "osinfo failed")
                return
            # TODO: insert into os_info
            mark_check(ctx.db, check_id, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, check_id, "run", str(e), -1)
            mark_check(ctx.db, check_id, "ERROR", str(e))
