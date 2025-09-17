from .base import AuditCheck, AuditContext
from . import register

@register
class Routes(AuditCheck):
    name="routes"; requires=("ip",)

    def probe(self, ctx: AuditContext)->bool:
        return ctx.ssh.which("ip")

    def run(self, ctx: AuditContext)->None:
        from utils.db import start_check, mark_check, record_error
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            # Current runtime routing + rules
            cur_routes = ctx.ssh.run("ip route show").out
            cur_rules  = ctx.ssh.run("ip rule show").out

            # Configured (persisted) routes (CentOS 7): sysconfig + NetworkManager
            cfg_concat = []
            cfg_concat.append(ctx.ssh.run("ls /etc/sysconfig/network-scripts/route-* 2>/dev/null || true").out)
            cfg_concat.append(ctx.ssh.run("for f in /etc/sysconfig/network-scripts/route-*; do [ -f \"$f\" ] && echo -e \"\\n## $f\" && cat \"$f\"; done 2>/dev/null || true").out)
            cfg_concat.append(ctx.ssh.run("for f in /etc/sysconfig/network-scripts/ifcfg-*; do [ -f \"$f\" ] && echo -e \"\\n## $f\" && egrep '^(NAME|DEVICE|BOOTPROTO|IPADDR|GATEWAY|PREFIX|ONBOOT)=' \"$f\"; done 2>/dev/null || true").out)
            if ctx.ssh.which("nmcli"):
                cfg_concat.append(ctx.ssh.run("nmcli -t -f connection.id,connection.type,ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.routes connection show || true").out)

            cfg_text = "\n".join([x for x in cfg_concat if x])
            # TODO: persist current, rules, and config into routing_state (three rows)
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
