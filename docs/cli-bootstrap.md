# CLI & Bootstrap

## Usage Examples
```
python auditron.py                 # interactive (resume/new)
python auditron.py --resume
python auditron.py --host 10.0.0.12 --skip nmap,file_snapshots --timeout 45
```

## Minimal `AuditCheck` Base
```python
from abc import ABC, abstractmethod

class AuditContext:
    def __init__(self, host, ssh, db, limits, clock):
        self.host = host; self.ssh = ssh; self.db = db
        self.limits = limits; self.clock = clock

class AuditCheck(ABC):
    name: str = "base"
    requires: tuple[str, ...] = ()
    @abstractmethod
    def probe(self, ctx: AuditContext) -> bool: ...
    @abstractmethod
    def run(self, ctx: AuditContext) -> None: ...
```
