from .base import AuditCheck
from .osinfo import OSInfo
from .processes import Processes
from .routes import Routes
from .rpm_inventory import RpmInventory
from .rpm_verify import RpmVerify
from .sockets import Sockets

REGISTRY = [OSInfo, RpmInventory, RpmVerify, Processes, Sockets, Routes]
