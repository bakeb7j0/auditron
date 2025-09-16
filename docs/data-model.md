# Data Model & ERD

Auditron stores **configuration, sessions, check runs, errors**, and **normalized artifacts** (packages, files, sockets, processes, etc.). Content blobs (changed text/configs) are gzip‑compressed and de‑duplicated by SHA‑256.

```mermaid
erDiagram
    HOSTS ||--o{ SESSIONS : audits
    SESSIONS ||--o{ CHECK_RUNS : contains
    CHECK_RUNS ||--o{ ERRORS : yields

    HOSTS {
      integer id PK
      string  hostname
      string  ip
      string  ssh_user
      string  ssh_key_path
      integer ssh_port
      boolean use_sudo
    }

    SESSIONS {
      integer id PK
      datetime started_at
      datetime finished_at
      string   initiated_by
      string   mode
    }

    CHECK_RUNS {
      integer id PK
      integer session_id FK
      integer host_id    FK
      string  check_name
      datetime started_at
      datetime finished_at
      string  status
      string  reason
    }

    ERRORS {
      integer id PK
      integer check_run_id FK
      string  stage
      text    stderr
      integer exit_code
    }
```
Further tables specialize results: `RPM_PACKAGES`, `RPM_VERIFIED_FILES`, `FILE_META`, `FILE_SNAPSHOTS`, `USERS`, `GROUPS`, `BASH_HISTORY`, `LOGIN_EVENTS`, `LISTEN_SOCKETS`, `PROCESSES`, `PROC_OPEN_FILES`, `SERVICES`, `NMAP_RESULTS`, `RESOURCE_SNAPSHOTS`, `DISK_USAGE`, `OS_INFO`, `FIREWALL_STATE`, `NET_INTERFACES`, `HW_*`.
