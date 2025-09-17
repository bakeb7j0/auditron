from .base import AuditCheck
from .osinfo import OSInfo
from .rpm_inventory import RpmInventory
from .rpm_verify import RpmVerify
from .processes import Processes

REGISTRY = [OSInfo, RpmInventory, RpmVerify, Processes]
