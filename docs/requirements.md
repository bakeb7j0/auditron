# Requirements

## Functional
- **SSH orchestration** of targets from a database; serial execution in v1 (future: concurrent pool).
- **Per‑check toggles:** Global defaults + per‑host overrides.
- **Checks (each individually toggleable):**
  1. **RPM — current inventory** and **verification** (`rpm -qa`, `rpm -Va`).
  2. **RPM — history** via `yum history` and `/var/log/yum.log*` (if present).
  3. **File change capture:** for modified RPM‑owned files, store metadata (mode, uid, gid, size, mtime, inode), SHA‑256, and **text/config contents** (size‑capped, compressed).
  4. **Users & Groups:** `getent passwd`, `getent group` + hostname.
  5. **Bash history** (timestamps if present).
  6. **Logins:** `last` (wtmp) and `lastb` (btmp) when available.
  7. **Listening sockets:** prefer `ss -lntu`, fallback `netstat -lpn --tcp --udp`.
  8. **Processes & open files:** `ps -eo ...`, `lsof -p` (fallback `/proc/.../fd`).
  9. **Services & runlevels:** `systemctl list-unit-files`, `systemctl get-default`.
  10. **Nmap:** orchestrator→target TCP/UDP discovery with service probes (optional).
  11. **Resource snapshot:** CPU/load, memory/swap, filesystem usage, uptime.
  12. **OS & kernel:** `/etc/centos-release`/`/etc/os-release`, `uname -srvm`.
  13. **Firewall:** firewalld zones/rules; fallback `iptables-save` snapshot.
  14. **Network interfaces & routes:** `ip -d addr`, `ip link`, `ip route`.
  15. **Hardware inventory:** `lspci -nnk`, `lsusb`, `lsblk -O -J`; optional `dmidecode`.
- **Progress feedback** for overall host list and per‑host per‑check status (SUCCESS/SKIP/ERROR).
- **Resumable sessions**; prompt to continue or start a new session.
- **Failure logging** for missing tools/permissions/timeouts per host/check.

## Non‑Functional
- **Portable:** Runs from USB; writes only to USB DB + logs.
- **Read‑only:** No changes to target configuration.
- **Performance:** Single host run in minutes (data-dependent).
- **Storage constraints:** Snapshot size caps, gzip compression, content dedupe by SHA‑256.
