import shlex
import subprocess


class SSHResult:
    def __init__(self, rc: int, out: str, err: str):
        self.rc = rc
        self.out = out
        self.err = err


class SSHClient:
    def __init__(self, host: dict, timeout: int = 60):
        self.host = host
        self.timeout = timeout
        self._which_cache = {}

    def which(self, binary: str) -> bool:
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
            )
            if check and p.returncode != 0:
                raise RuntimeError(f"SSH failed rc={p.returncode}: {p.stderr}")
            return SSHResult(p.returncode, p.stdout, p.stderr)
        except subprocess.TimeoutExpired:
            return SSHResult(124, "", f"timeout after {self.timeout}s")
