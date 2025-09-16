# Overview

**Auditron** is a self‑contained, USB‑hosted auditing tool. From an orchestrator host, it SSHes into a configured list of CentOS 7.6 targets, runs a curated set of checks, and stores **both configuration and results** in a SQLite database **on the USB drive**.

## Goals
- **Portability:** zero/minimal install on targets (agentless via SSH).
- **Determinism:** stick to CentOS 7.x tooling with predictable output.
- **Resilience:** resumable sessions; explicit logging of skipped checks/unavailable tools.
- **Modularity:** Strategy pattern for checks; minimal coupling.
- **Data fidelity:** normalized schema; optional content snapshots with caps and compression.

## Non‑Goals (initial release)
- Concurrent multi‑host execution (kept in mind for vNext).
- Non‑CentOS 7 targets (extend later via capability discovery).
- Any configuration changes on targets (read‑only by design).

## Primary Use Cases
1. **Fleet baseline capture** of packages, services, listeners, users/groups, OS/kernel, firewall.
2. **Change/drift detection** via RPM verification and text/config snapshots.
3. **Forensics snapshot** of logins, bash history, processes/open files, network topology.
4. **Compliance evidence** for service/runlevel enablement and firewall posture.
