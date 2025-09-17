from abc import ABC, abstractmethod

class AuditContext:
    """
    Carries per-host state for audit checks.
    Includes host config, SSH client, DB handle, and runtime limits.
    """
    def __init__(self, host: dict, ssh, db, limits: dict, clock):
        self.host = host
        self.ssh = ssh
        self.db = db
        self.limits = limits
        self.clock = clock
        self.session_id = None

class AuditCheck(ABC):
    """
    Strategy base class.
    Each audit check implements probe() to decide applicability
    and run() to execute the check.
    """
    name: str = "base"
    requires: tuple[str, ...] = ()

    @abstractmethod
    def probe(self, ctx: AuditContext) -> bool:
        """Return True if prerequisites (binaries, permissions) are met."""
        ...

    @abstractmethod
    def run(self, ctx: AuditContext) -> None:
        """Execute the audit check and persist results into DB."""
        ...
