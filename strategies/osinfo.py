from .base import AuditCheck, AuditContext


class OSInfo(AuditCheck):
    name = "osinfo"
    requires: tuple[str, ...] = ()

    def probe(self, ctx: AuditContext) -> bool:
        return True

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res_os = ctx.ssh.run("if [ -f /etc/os-release ]; then . /etc/os-release; echo \"$NAME|$VERSION_ID|$ID\"; else cat /etc/centos-release; fi")
            res_uname = ctx.ssh.run("uname -srmo")
            if res_os.rc != 0 or res_uname.rc != 0:
                record_error(ctx.db, cid, "run", (res_os.err or '') + (res_uname.err or ''), res_os.rc or res_uname.rc)
                mark_check(ctx.db, cid, "ERROR", "osinfo failed"); return
            name, version_id, osid = (res_os.out.strip().split("|") + ["", "", ""])[:3]
            kernel_arch = res_uname.out.strip()
            ctx.db.execute("INSERT INTO os_info(host_id,name,version_id,kernel,arch) VALUES (?,?,?,?,?)",
                           (ctx.host["id"], name, version_id, kernel_arch, ""))
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
