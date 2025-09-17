from .base import AuditCheck
from .osinfo import OSInfo
from .rpm_inventory import RpmInventory
from .rpm_verify import RpmVerify
from .processes import Processes
from .sockets import Sockets
from .routes import Routes

REGISTRY = [OSInfo, RpmInventory, RpmVerify, Processes, Sockets, Routes]
