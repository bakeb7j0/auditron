# Requirements — EARS Syntax (Authoritative)

Legend:  
Ubiquitous form: “The system shall …”  
Event-driven: “When <trigger>, the system shall …”  
State-driven: “While <state>, the system shall …”  
Unwanted: “Where <condition>, the system shall …”  
Optional feature: “Where <feature is enabled>, the system shall …”

## Core Orchestration
- **REQ-U-001** The system shall read target hosts from the SQLite database located on the USB drive.
- **REQ-U-002** The system shall connect to each target host via SSH using the configured user, key path, and port.
- **REQ-U-003** The system shall execute audit checks in **serial** for v1.
- **REQ-U-004** The system shall implement each audit check as a Strategy plug-in with `probe()` and `run()`.

## Configuration & Overrides
- **REQ-U-010** The system shall maintain **global defaults** that enable or disable each check.
- **REQ-U-011** The system shall support **per-host overrides** that supersede global defaults for any check.
- **REQ-U-012** The system shall allow configuration of snapshot limits, gzip usage, and command timeouts globally and per host.
- **REQ-E-013** When the user edits configuration via the console utility, the system shall persist changes only on explicit confirmation (e.g., menu actions).

## Execution Control & Resume
- **REQ-U-020** The system shall record audit **sessions** and **per-check** statuses in the database.
- **REQ-E-021** When a previous session is incomplete, the system shall prompt the user to **resume** or **start a new** session.
- **REQ-U-022** The system shall mark each check as **SUCCESS**, **SKIP**, or **ERROR** with an associated reason where applicable.

## Progress & Logging
- **REQ-U-030** The system shall display progress for host iteration and per-check execution.
- **REQ-U-031** The system shall log missing prerequisites and failures per host/check.

## Data Capture — Packages & Files
- **REQ-U-040** The system shall list installed RPMs with name, epoch, version, release, arch, and install time.
- **REQ-U-041** The system shall verify RPM-owned files and capture verify flags.
- **REQ-U-042** The system shall, for modified RPM-owned **text/config** files, capture file metadata and a size-capped, gzip-compressed content snapshot.
- **REQ-U-043** The system shall record RPM history using `yum history` and available yum logs.

## Identity & Activity
- **REQ-U-050** The system shall record users and groups via `getent`.
- **REQ-U-051** The system shall capture bash history entries (including timestamps where present) per user, including root.
- **REQ-U-052** The system shall capture successful and failed login events via `last` and `lastb`.

## Network & Services
- **REQ-U-060** The system shall record listening sockets using `ss` (or `netstat` as fallback).
- **REQ-U-061** The system shall record running processes with command line and user; optionally open files where available.
- **REQ-U-062** The system shall record services and enablement state using `systemctl` and the default target.
- **REQ-O-063** Where Nmap scanning is enabled, the system shall scan each host for TCP/UDP ports and store results.

## Routing (NEW)
- **REQ-U-070** The system shall capture the **current** routing table via `ip route show` and policy rules via `ip rule show`.
- **REQ-U-071** The system shall capture the **configured** routing state that would apply after reboot, including:
  - `/etc/sysconfig/network-scripts/route-*` and relevant `ifcfg-*` settings;
  - NetworkManager connection routing properties via `nmcli`, where available.

## System Info & Security Posture
- **REQ-U-080** The system shall record OS name/version and kernel details.
- **REQ-U-081** The system shall capture CPU/memory/swap and filesystem usage snapshots.
- **REQ-U-082** The system shall capture firewall state via firewalld (zones/rules) or `iptables-save` as fallback.
- **REQ-U-083** The system shall enumerate network interfaces and routes.
- **REQ-U-084** The system shall gather hardware summaries (`lspci`, `lsusb`, `lsblk`) and, where permitted, `dmidecode`.

## Security & Privacy
- **REQ-U-090** The system shall operate in a read-only manner and shall not modify target configuration.
- **REQ-U-091** The system shall avoid capturing secrets and shall enforce allow/deny path globs for snapshots.
- **REQ-U-092** The system shall normalize timestamps to UTC.

## Console Configuration Utility
- **REQ-U-100** The system shall provide a menu-based console utility to add/remove hosts, toggle global defaults, and set per-host overrides.
- **REQ-U-101** The console utility shall present options to save changes and quit, or quit without saving.

## Non-Goals (v1)
- **REQ-U-110** The system shall not perform concurrent multi-host execution (future enhancement).
