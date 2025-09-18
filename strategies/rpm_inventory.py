from utils.db import mark_check, record_error, start_check

from .base import AuditCheck, AuditContext


class RpmInventory(AuditCheck):
    name = "rpm_inventory"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return bool(ctx.ssh.which("rpm"))

    def run(self, ctx: AuditContext) -> None:
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            fmt = "%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\\n"
            res = ctx.ssh.run(f"rpm -qa --qf '{fmt}'")
            if res.rc != 0:
                record_error(ctx.db, cid, "run", res.err, res.rc)
                mark_check(ctx.db, cid, "ERROR", "rpm -qa failed")
                return

            rows: list[tuple] = []
            for ln in (ln for ln in res.out.splitlines() if ln.strip()):
                parts = (ln.split("|") + ["", "", "", "", "", ""])[:6]
                name, epoch, ver, rel, arch, inst = parts
                try:
                    inst_val = int(inst)
                except ValueError:
                    inst_val = None
                rows.append((ctx.host["id"], name, epoch, ver, rel, arch, inst_val))

            if rows:
                ctx.db.executemany(
                    "INSERT INTO rpm_packages(host_id,name,epoch,version,release,arch,install_time) VALUES (?,?,?,?,?,?,?)",
                    rows,
                )
                ctx.db.commit()

            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:  # noqa: BLE001 - keep broad to log unexpected failures
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
