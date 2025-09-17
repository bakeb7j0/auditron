from .base import AuditCheck, AuditContext


class Routes(AuditCheck):
    name = "routes"
    requires = ("ip",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("ip")

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check, ts
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            cur_routes = ctx.ssh.run("ip route show || true").out
            cur_rules  = ctx.ssh.run("ip rule show || true").out
            cfg_parts = []
            cfg_parts.append(ctx.ssh.run("for f in /etc/sysconfig/network-scripts/route-*; do [ -f \"$f\" ] && echo -e \"\\n## $f\" && cat \"$f\"; done 2>/dev/null || true").out)
            cfg_parts.append(ctx.ssh.run("for f in /etc/sysconfig/network-scripts/ifcfg-*; do [ -f \"$f\" ] && echo -e \"\\n## $f\" && egrep '^(NAME|DEVICE|BOOTPROTO|IPADDR|GATEWAY|PREFIX|ONBOOT)=' \"$f\"; done 2>/dev/null || true").out)
            if ctx.ssh.which("nmcli"):
                cfg_parts.append(ctx.ssh.run("nmcli -t -f connection.id,connection.type,ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.routes connection show || true").out)
            cfg_text = "\n".join([p for p in cfg_parts if p])

            now = ts()
            ctx.db.execute("INSERT INTO routing_state(host_id,kind,content,captured_at) VALUES (?,?,?,?)", (ctx.host["id"], "current", cur_routes, now))
            ctx.db.execute("INSERT INTO routing_state(host_id,kind,content,captured_at) VALUES (?,?,?,?)", (ctx.host["id"], "rules", cur_rules, now))
            ctx.db.execute("INSERT INTO routing_state(host_id,kind,content,captured_at) VALUES (?,?,?,?)", (ctx.host["id"], "config", cfg_text, now))
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
