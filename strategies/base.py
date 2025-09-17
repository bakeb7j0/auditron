from abc import ABC, abstractmethod
class AuditContext:
    def __init__(self, host: dict, ssh, db, limits: dict, clock):
        self.host=host; self.ssh=ssh; self.db=db; self.limits=limits; self.clock=clock
        self.session_id=None
class AuditCheck(ABC):
    name: str = "base"
    requires: tuple[str,...] = ()
    @abstractmethod
    def probe(self, ctx: AuditContext) -> bool: ...
    @abstractmethod
    def run(self, ctx: AuditContext) -> None: ...
