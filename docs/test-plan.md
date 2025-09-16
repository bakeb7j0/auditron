# Test Plan (v1)

## Unit Tests
- Parsers: rpm verify, yum history, `ss`/`netstat`, `last`/`lastb`, size‑cap & gzip/dedupe.
- Strategy lifecycle: `probe()` SKIP reasons; `run()` happy path; error persistence.

## Integration (VM)
- Missing `lsof` ⇒ open‑files gracefully SKIP.
- Firewalld inactive ⇒ fallback to `iptables-save`.
- Non‑root SSH ⇒ sudo elevation for protected files.
- Large config snapshot ⇒ truncated to cap; length recorded.

## Resume Logic
- Interrupt mid‑run (host 2, check 3). On restart, choose **resume** and verify continuation from pending check.
