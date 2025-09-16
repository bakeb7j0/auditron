import re, json, time

def parse_rpm_verify(output: str):
    # Very simple placeholder parser: lines like 'SM5DLUGT. c /etc/foo.conf'
    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line: continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            flags, path = parts
            rows.append((flags, path))
    return rows
