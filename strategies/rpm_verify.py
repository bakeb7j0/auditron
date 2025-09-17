import base64
import shlex
import sqlite3

from utils.compress import gz_bytes, sha256_bytes
from utils.parsing import parse_rpm_verify

from .base import AuditCheck, AuditContext


class RpmVerify(AuditCheck):
    name = "rpm_verify"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return ctx.ssh.which("rpm")

    def _capture_meta(self, ctx: AuditContext, path: str):
        stat = ctx.ssh.run("stat -Lc '%f|%u|%g|%s|%Y|%i' {}".format(shlex.quote(path)))
        sha = ctx.ssh.run("sha256sum {} 2>/dev/null | awk '{{print $1}}' || true".format(shlex.quote(path)))
        mode, uid, gid, size, mtime, inode = (stat.out.strip().split('|')+['','','','',''])[:6]
        try:
            size = int(size) if size else None
            uid = int(uid) if uid else None
            gid = int(gid) if gid else None
            mtime = int(mtime) if mtime else None
            # If inode looks hex (starts with 0x), parse base 16; else base 10
            if inode:
                inode = int(inode, 16) if inode.lower().startswith('0x') else int(inode, 10)
            else:
                inode = None
        except Exception:
            pass
        mode_int = int(mode, 16) if mode else None
        return dict(mode=mode_int, uid=uid, gid=gid, size=size, mtime=mtime, inode=inode, sha=sha.out.strip())

    def _is_textish(self, ctx: AuditContext, path: str) -> bool:
        mime = ctx.ssh.run("file -b --mime-type {} 2>/dev/null || echo text/plain".format(shlex.quote(path))).out.strip()
        return (mime.startswith("text/") or mime.endswith("+xml") or mime.endswith("/json") or mime.endswith("/xml"))

    def _snapshot(self, ctx: AuditContext, path: str):
        lim = int(ctx.limits.get("max_snapshot_bytes", 524288))
        sizeq = ctx.ssh.run("stat -Lc %s {} 2>/dev/null || echo 0".format(shlex.quote(path)))
        try:
            size = int(sizeq.out.strip())
        except Exception:
            size = 0
        if size <= 0 or size > lim:
            return None, None, None
        if not self._is_textish(ctx, path):
            return None, None, None
        b64 = ctx.ssh.run("base64 -w0 {} 2>/dev/null || true".format(shlex.quote(path))).out.strip()
        if not b64:
            return None, None, None
        raw = base64.b64decode(b64.encode('utf-8'))
        gz = gz_bytes(raw) if int(ctx.limits.get("gzip_snapshots", 1)) else raw
        sha = sha256_bytes(raw)
        return gz, len(raw), sha

    def run(self, ctx: AuditContext) -> None:
        from utils.db import mark_check, record_error, start_check, ts
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res = ctx.ssh.run("rpm -Va --nodigest --nosignature || true")
            lines = [l for l in res.out.splitlines() if l.strip()]
            for ln in lines:
                parsed = parse_rpm_verify(ln)
                if not parsed:
                    continue
                flags, path = parsed[0]
                meta = self._capture_meta(ctx, path)
                ctx.db.execute(
                    "INSERT INTO file_meta(path, mode, uid, gid, size, mtime, inode, sha256) VALUES (?,?,?,?,?,?,?,?)",
                    (path, meta.get('mode'), meta.get('uid'), meta.get('gid'), meta.get('size'), meta.get('mtime'), meta.get('inode'), meta.get('sha'))
                )
                meta_id = ctx.db.execute("SELECT last_insert_rowid()").fetchone()[0]
                snap_id = None
                gz, length, sha = self._snapshot(ctx, path)
                if gz is not None:
                    ctx.db.execute(
                        "INSERT INTO file_snapshots(sha256, content_gz, length_bytes, mime, captured_at) VALUES (?,?,?,?,?)",
                        (sha, sqlite3.Binary(gz), length, "text/plain", ts())
                    )
                    snap_id = ctx.db.execute("SELECT last_insert_rowid()").fetchone()[0]
                ctx.db.execute(
                    "INSERT INTO rpm_verified_files(host_id, package_id, path, verify_flags, changed, snapshot_id, meta_id) VALUES (?,?,?,?,?,?,?)",
                    (ctx.host["id"], None, path, flags, 1, snap_id, meta_id)
                )
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
