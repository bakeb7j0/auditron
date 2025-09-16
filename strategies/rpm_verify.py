from .base import AuditCheck, AuditContext
from . import register

@register
class RpmVerify(AuditCheck):
    name = "rpm_verify"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("rpm")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import start_check, mark_check, record_error
        from utils.parsing import parse_rpm_verify
        check_id = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res = ctx.ssh.run("rpm -Va")
            if res.rc != 0 and res.out.strip() == "":
                record_error(ctx.db, check_id, "run", res.err, res.rc)
                mark_check(ctx.db, check_id, "ERROR", "rpm -Va failed")
                return
            # TODO: parse flags/paths and persist to rpm_verified_files/file_meta/file_snapshots
            _rows = parse_rpm_verify(res.out)
            mark_check(ctx.db, check_id, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, check_id, "run", str(e), -1)
            mark_check(ctx.db, check_id, "ERROR", str(e))
