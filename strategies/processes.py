from .base import AuditCheck, AuditContext


class Processes(AuditCheck):
    name = "processes"
    requires = ("ps",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("ps")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check

        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            ctx.db.execute("DELETE FROM processes WHERE host_id=?", (ctx.host["id"],))
            res = ctx.ssh.run("ps -eo pid,ppid,user,lstart,etime,cmd --no-headers")
            if res.rc != 0 and not res.out.strip():
                record_error(ctx.db, cid, "run", res.err, res.rc)
                mark_check(ctx.db, cid, "ERROR", "ps failed")
                return
            for line in res.out.splitlines():
                if not line.strip():
                    continue
                parts = line.split(None, 6)
                if len(parts) < 7:
                    continue
                pid, ppid, user, w1, w2, w3, rest = parts
                start_time = " ".join([w1, w2, w3])
                etime_cmd = rest.split(None, 1)
                etime = etime_cmd[0]
                cmd = etime_cmd[1] if len(etime_cmd) > 1 else ""
                ctx.db.execute(
                    "INSERT INTO processes(host_id,pid,ppid,user,start_time,etime,cmd) VALUES (?,?,?,?,?,?,?)",
                    (ctx.host["id"], int(pid), int(ppid), user, start_time, etime, cmd),
                )
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
