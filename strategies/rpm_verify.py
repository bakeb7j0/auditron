import base64
import shlex
from typing import Optional

from utils.compress import gz_bytes, sha256_bytes
from utils.db import mark_check, record_error, start_check, ts
from utils.parsing import parse_rpm_verify

from .base import AuditCheck, AuditContext


class RpmVerify(AuditCheck):
    name = "rpm_verify"
    requires = ("rpm",)

    def probe(self, ctx: AuditContext) -> bool:
        return bool(ctx.ssh.which("rpm"))

    def _stat_meta(self, ctx: AuditContext, path_q: str) -> tuple[
        Optional[int],
        Optional[int],
        Optional[int],
        Optional[int],
        Optional[int],
        Optional[int],
    ]:
        # mode(hex), uid, gid, size, mtime, inode
        stat_cmd = f"stat -c '%f|%u|%g|%s|%Y|%i' {path_q}"
        stat_res = ctx.ssh.run(stat_cmd)
        if stat_res.rc == 0 and stat_res.out.strip():
            fhex, uid, gid, size, mtime, inode = (
                stat_res.out.strip().split("|") + ["0", "0", "0", "0", "0", "0"]
            )[:6]
            try:
                mode = int(fhex, 16)
            except ValueError:
                mode = None
            return mode, int(uid), int(gid), int(size), int(mtime), int(inode)
        return None, None, None, None, None, None

    def run(self, ctx: AuditContext) -> None:
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            res = ctx.ssh.run("rpm -Va --nodigest --nosignature || true")
            for flags, path in parse_rpm_verify(res.out):
                changed = 0 if set(flags) <= {"."} else 1
                path_q = shlex.quote(path)

                # File meta
                mode, uid, gid, size, mtime, inode = self._stat_meta(ctx, path_q)
                meta_id = None
                if any(v is not None for v in (mode, uid, gid, size, mtime, inode)):
                    ctx.db.execute(
                        "INSERT INTO file_meta(path, mode, uid, gid, size, mtime, inode, sha256) VALUES (?,?,?,?,?,?,?,?)",
                        (path, mode, uid, gid, size, mtime, inode, None),
                    )
                    meta_id = int(
                        ctx.db.execute("SELECT last_insert_rowid()").fetchone()[0]
                    )

                # Snapshot for text-like changed files
                snapshot_id = None
                if changed:
                    file_cmd = f"head -c 512 {path_q} | file -b -"
                    file_res = ctx.ssh.run(file_cmd)
                    if file_res.rc == 0 and (
                        "text" in file_res.out.lower()
                        or "ascii" in file_res.out.lower()
                    ):
                        cat_res = ctx.ssh.run(f"cat {path_q}")
                        if cat_res.rc == 0:
                            data = cat_res.out.encode("utf-8", errors="ignore")
                            sha_hex = sha256_bytes(data)
                            gz = gz_bytes(data)
                            ctx.db.execute(
                                "INSERT INTO file_snapshots(path, mode, uid, gid, size, mtime, inode, sha256, gz_len, gz_b64, captured_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (
                                    path,
                                    mode,
                                    uid,
                                    gid,
                                    size,
                                    mtime,
                                    inode,
                                    sha_hex,
                                    len(gz),
                                    base64.b64encode(gz).decode("ascii"),
                                    ts(),
                                ),
                            )
                            snapshot_id = int(
                                ctx.db.execute("SELECT last_insert_rowid()").fetchone()[
                                    0
                                ]
                            )

                # Link row
                ctx.db.execute(
                    "INSERT INTO rpm_verified_files(host_id, package_id, path, verify_flags, changed, snapshot_id, meta_id) VALUES (?,?,?,?,?,?,?)",
                    (ctx.host["id"], None, path, flags, changed, snapshot_id, meta_id),
                )

            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:  # noqa: BLE001
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
