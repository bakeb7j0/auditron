from .base import AuditCheck, AuditContext


class RpmInventory(AuditCheck):
    name = "rpm_inventory"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("rpm")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            ctx.db.execute("DELETE FROM rpm_packages WHERE host_id=?", (ctx.host["id"],))
            res = ctx.ssh.run("rpm -qa --qf '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\\n'")
            if res.rc != 0:
                record_error(ctx.db, cid, "run", res.err, res.rc); mark_check(ctx.db, cid, "ERROR", "rpm -qa failed"); return
            rows = []
            for line in res.out.splitlines():
                if not line.strip(): continue
                name, epoch, ver, rel, arch, inst = (line.split("|") + ["","","","","",""])[:6]
                try: inst = int(inst)
                except: inst = None
                rows.append((ctx.host["id"], name, epoch, ver, rel, arch, inst))
            ctx.db.executemany(
                "INSERT INTO rpm_packages(host_id,name,epoch,version,release,arch,install_time) VALUES (?,?,?,?,?,?,?)",
                rows
            )
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
