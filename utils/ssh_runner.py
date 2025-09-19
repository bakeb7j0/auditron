"""SSH client utilities for remote command execution.

Provides SSH client wrapper for executing commands on remote hosts
with timeout handling and result encapsulation.
"""

import shlex
import subprocess


class SSHResult:
    """Encapsulates the result of an SSH command execution.

    Attributes:
        rc: Command exit code
        out: Standard output from command
        err: Standard error from command
    """

    def __init__(self, rc: int, out: str, err: str):
        self.rc = rc
        self.out = out
        self.err = err


class SSHClient:
    """SSH client for executing commands on remote hosts.

    Provides connection management, command execution with timeouts,
    and tool availability caching for efficient audit operations.
    """

    def __init__(self, host: dict, timeout: int = 60):
        """Initialize SSH client for specific host.

        Args:
            host: Host configuration dictionary with connection details
            timeout: Command execution timeout in seconds
        """
        self.host = host
        self.timeout = timeout
        self._which_cache = {}

    def which(self, binary: str) -> bool:
        """Check if binary exists on remote host (cached).

        Args:
            binary: Name of binary to check for

        Returns:
            True if binary exists and is executable, False otherwise
        """
        if binary in self._which_cache:
            return self._which_cache[binary]
        cmd = f"command -v {shlex.quote(binary)} || which {shlex.quote(binary)}"
        res = self.run(cmd, check=False)
        ok = res.rc == 0 and res.out.strip() != ""
        self._which_cache[binary] = ok
        return ok

    def run(
        self, command: str, check: bool = False, use_sudo: bool | None = None
    ) -> SSHResult:
        """Execute command on remote host via SSH.

        Args:
            command: Command to execute on remote host
            check: If True, raise exception on non-zero exit code
            use_sudo: Override host sudo setting for this command

        Returns:
            SSHResult containing exit code, stdout, and stderr

        Raises:
            RuntimeError: If check=True and command fails
        """
        user = self.host.get("ssh_user") or "root"
        key = self.host.get("ssh_key_path")
        ip = self.host.get("ip") or self.host.get("hostname")
        port = str(self.host.get("ssh_port") or 22)
        sudo = self.host.get("use_sudo", 1) if use_sudo is None else use_sudo
        remote_cmd = command if not sudo else f"sudo -n bash -lc {shlex.quote(command)}"
        ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-p", port]
        if key:
            ssh_cmd += ["-i", key]
        ssh_cmd += [f"{user}@{ip}", remote_cmd]
        try:
            p = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False,  # We handle return codes manually
            )
            if check and p.returncode != 0:
                raise RuntimeError(f"SSH failed rc={p.returncode}: {p.stderr}")
            return SSHResult(p.returncode, p.stdout, p.stderr)
        except subprocess.TimeoutExpired:
            return SSHResult(124, "", f"timeout after {self.timeout}s")
