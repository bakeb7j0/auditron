# Check Specifications (CentOS 7.6 Friendly)

## RPM — Inventory & Verification
- **List:** `rpm -qa --qf '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\n'`
- **Verify:** `rpm -Va` (flags like `SM5DLUGT...` + path)
- **On changed files:** collect metadata (mode, uid, gid, size, mtime, inode), SHA‑256; if text/config, store content snapshot (size‑capped, gzip). MIME detect via `file -b --mime-type`.

## RPM — History
- `yum history list all`, `yum history info <id>`; supplement with `/var/log/yum.log*` when present. Store tx id, user, cmdline, action, pkgs, timestamps.

## Users & Groups
- `getent passwd`, `getent group`; also capture `hostname`/`hostnamectl`.

## Bash History
- Files: `/home/*/.bash_history`, `/root/.bash_history`. Timestamp lines `# 1694389172` → normalize to UTC; store `uid`, `command`, `source_file`, `line_no`.

## Login Events
- Successful: `last -w` (wtmp). Failed: `lastb -w` (btmp if present). Store user, src, tty, login/logout, duration, outcome.

## Listening Sockets
- Prefer `ss -lntu` (+ `ss -lptn`); fallback `netstat -lpn --tcp --udp`. Store proto, addr:port, state, pid/process if available.

## Processes & Open Files
- `ps -eo pid,ppid,user,lstart,etime,cmd`.
- Open files via `lsof -p <pid>`; fallback to `/proc/<pid>/fd` and `/proc/<pid>/maps` enumeration.

## Services & Runlevels
- `systemctl list-unit-files --type=service`, `systemctl get-default`. Optional snapshots of `systemctl status <svc>` for enabled services (size‑limited).

## Nmap (Optional)
- `nmap -sS -sU -Pn -T4 -oX - <host>`; store XML (size‑limited) or parsed open ports + service/version.

## Resource Snapshot
- CPU/load: `top -b -n1 | head -n 5`, `uptime`
- Memory: `free -m`
- Disks: `df -TP`

## OS & Kernel
- OS: `/etc/centos-release` or `/etc/os-release`.
- Kernel: `uname -srvm`

## Firewall
- Firewalld: `systemctl is-active firewalld`, then `firewall-cmd --get-default-zone` and `--list-all` (per zone).
- Fallback: `iptables-save` snapshot.

## Network Interfaces
- `ip -d addr show`, `ip link`, `ip route`

## Hardware Inventory
- `lspci -nnk`, `lsusb`, `lsblk -O -J`; optional `dmidecode -t system,baseboard,bios,processor,memory`
