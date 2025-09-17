from .base import AuditCheck
from .osinfo import OSInfo
from .rpm_inventory import RpmInventory
from .rpm_verify import RpmVerify

REGISTRY = [OSInfo, RpmInventory, RpmVerify]
