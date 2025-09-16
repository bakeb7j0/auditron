PRAGMA foreign_keys=ON;

-- Core
CREATE TABLE IF NOT EXISTS hosts (
  id INTEGER PRIMARY KEY,
  hostname TEXT NOT NULL,
  ip TEXT,
  ssh_user TEXT,
  ssh_key_path TEXT,
  ssh_port INTEGER DEFAULT 22,
  use_sudo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  initiated_by TEXT,
  mode TEXT CHECK (mode IN ('new','resume'))
);

CREATE TABLE IF NOT EXISTS check_runs (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  check_name TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  status TEXT CHECK (status IN ('SUCCESS','SKIP','ERROR')),
  reason TEXT
);

CREATE TABLE IF NOT EXISTS errors (
  id INTEGER PRIMARY KEY,
  check_run_id INTEGER NOT NULL REFERENCES check_runs(id) ON DELETE CASCADE,
  stage TEXT,
  stderr TEXT,
  exit_code INTEGER
);

-- Config
CREATE TABLE IF NOT EXISTS global_defaults (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  rpm_inventory INTEGER DEFAULT 1,
  rpm_history INTEGER DEFAULT 1,
  rpm_verify INTEGER DEFAULT 1,
  file_snapshots INTEGER DEFAULT 1,
  users INTEGER DEFAULT 1,
  groups INTEGER DEFAULT 1,
  bash_history INTEGER DEFAULT 1,
  logins INTEGER DEFAULT 1,
  sockets INTEGER DEFAULT 1,
  processes INTEGER DEFAULT 1,
  services INTEGER DEFAULT 1,
  nmap INTEGER DEFAULT 1,
  resources INTEGER DEFAULT 1,
  osinfo INTEGER DEFAULT 1,
  firewall INTEGER DEFAULT 1,
  netif INTEGER DEFAULT 1,
  hw INTEGER DEFAULT 1,
  max_snapshot_bytes INTEGER DEFAULT 524288,
  gzip_snapshots INTEGER DEFAULT 1,
  command_timeout_sec INTEGER DEFAULT 60
);

CREATE TABLE IF NOT EXISTS host_overrides (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  rpm_inventory INTEGER, rpm_history INTEGER, rpm_verify INTEGER, file_snapshots INTEGER,
  users INTEGER, groups INTEGER, bash_history INTEGER, logins INTEGER, sockets INTEGER,
  processes INTEGER, services INTEGER, nmap INTEGER, resources INTEGER, osinfo INTEGER,
  firewall INTEGER, netif INTEGER, hw INTEGER,
  max_snapshot_bytes INTEGER,
  gzip_snapshots INTEGER,
  command_timeout_sec INTEGER
);

-- RPM inventory / verify
CREATE TABLE IF NOT EXISTS rpm_packages (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  name TEXT, epoch TEXT, version TEXT, release TEXT, arch TEXT,
  install_time INTEGER
);
CREATE INDEX IF NOT EXISTS ix_rpm_pkg_host_name ON rpm_packages(host_id, name);

CREATE TABLE IF NOT EXISTS file_meta (
  id INTEGER PRIMARY KEY,
  path TEXT,
  mode INTEGER, uid INTEGER, gid INTEGER, size INTEGER, mtime INTEGER, inode INTEGER,
  sha256 TEXT
);
CREATE INDEX IF NOT EXISTS ix_file_meta_path ON file_meta(path);

CREATE TABLE IF NOT EXISTS file_snapshots (
  id INTEGER PRIMARY KEY,
  sha256 TEXT UNIQUE,
  content_gz BLOB,
  length_bytes INTEGER,
  mime TEXT,
  captured_at TEXT
);

CREATE TABLE IF NOT EXISTS rpm_verified_files (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  package_id INTEGER REFERENCES rpm_packages(id) ON DELETE CASCADE,
  path TEXT,
  verify_flags TEXT,
  changed INTEGER,
  snapshot_id INTEGER REFERENCES file_snapshots(id),
  meta_id INTEGER REFERENCES file_meta(id)
);

-- Identity
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  uid INTEGER,
  name TEXT,
  home TEXT,
  shell TEXT
);

CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  gid INTEGER,
  name TEXT
);

CREATE TABLE IF NOT EXISTS bash_history (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  uid INTEGER,
  ts_utc TEXT,
  command TEXT,
  source_file TEXT,
  line_no INTEGER
);

CREATE TABLE IF NOT EXISTS login_events (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  user TEXT,
  src TEXT,
  tty TEXT,
  login_time TEXT,
  logout_time TEXT,
  duration_sec INTEGER,
  outcome TEXT
);

-- Network & processes
CREATE TABLE IF NOT EXISTS listen_sockets (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  proto TEXT,
  local TEXT,
  state TEXT,
  pid INTEGER,
  process TEXT
);

CREATE TABLE IF NOT EXISTS processes (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  pid INTEGER,
  ppid INTEGER,
  user TEXT,
  start_time TEXT,
  etime TEXT,
  cmd TEXT
);

CREATE TABLE IF NOT EXISTS proc_open_files (
  id INTEGER PRIMARY KEY,
  process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
  path TEXT
);

-- Services
CREATE TABLE IF NOT EXISTS services (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  name TEXT,
  state TEXT,
  target TEXT
);

-- Nmap
CREATE TABLE IF NOT EXISTS nmap_results (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  scan_xml_gz BLOB
);

-- Resources / Disks / OS / Firewall / NetIf / HW
CREATE TABLE IF NOT EXISTS resource_snapshots (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  load1 REAL, load5 REAL, load15 REAL,
  mem_total_mb INTEGER, mem_used_mb INTEGER,
  swap_total_mb INTEGER, swap_used_mb INTEGER,
  captured_at TEXT
);

CREATE TABLE IF NOT EXISTS disk_usage (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  fs TEXT, type TEXT, size_mb INTEGER, used_mb INTEGER, avail_mb INTEGER, use_pct INTEGER, mount TEXT
);

CREATE TABLE IF NOT EXISTS os_info (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  name TEXT, version_id TEXT, kernel TEXT, arch TEXT
);

CREATE TABLE IF NOT EXISTS firewall_state (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  mode TEXT, snapshot TEXT
);

CREATE TABLE IF NOT EXISTS net_interfaces (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  name TEXT, mac TEXT, mtu INTEGER, state TEXT, addrs_json TEXT
);

CREATE TABLE IF NOT EXISTS hw_pci (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  line TEXT
);

CREATE TABLE IF NOT EXISTS hw_usb (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  line TEXT
);

CREATE TABLE IF NOT EXISTS hw_block (
  id INTEGER PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
  json TEXT
);
