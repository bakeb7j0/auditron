from abc import ABC, abstractmethod
from typing import Any, Optional


class AuditContext:
    def __init__(
        self,
        host: dict,
        ssh: Any,
        db: Any,
        limits: dict,
        clock: Any,
        session_id: Optional[int] = None,
    ):
        self.host = host
        self.ssh = ssh
        self.db = db
        self.limits = limits
        self.clock = clock
        self.session_id = session_id


class AuditCheck(ABC):
    name: str = "base"
    requires: tuple[str, ...] = ()

    def probe(self, ctx: "AuditContext") -> bool:
        return True

    @abstractmethod
    def run(self, ctx: "AuditContext") -> None: ...
