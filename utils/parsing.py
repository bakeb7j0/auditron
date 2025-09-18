import re


def parse_rpm_verify(output: str):
    rows = []
    for line in output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            flags, path = parts
            path = path.strip()
            if path.startswith(("c ", "d ")):
                path = path.split()[-1]
            rows.append((flags, path))
    return rows


_re_ss_pid = re.compile(r'users:\(\("([^"]+)",pid=(\d+)')


def parse_ss_listen(line: str):
    cols = line.split()
    if not cols:
        return None
    proto = cols[0]
    state = cols[1] if len(cols) > 1 else ""
    local = cols[4] if len(cols) > 4 else ""
    m = _re_ss_pid.search(line)
    pid = int(m.group(2)) if m else None
    proc = m.group(1) if m else None
    return proto, local, state, pid, proc
