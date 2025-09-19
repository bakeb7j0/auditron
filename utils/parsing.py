"""Command output parsing utilities for Auditron.

Provides parsers for various system command outputs including
RPM verification and network socket information.
"""

import re


def parse_rpm_verify(output: str):
    """Parse rpm -Va output into structured data.

    Args:
        output: Raw output from rpm -Va command

    Returns:
        List of tuples containing (verify_flags, file_path)
    """
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
    """Parse ss command output line for listening socket information.

    Args:
        line: Single line of ss command output

    Returns:
        Tuple of (protocol, local_address, state, pid, process_name)
        or None if line cannot be parsed
    """
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
