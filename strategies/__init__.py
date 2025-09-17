from .base import AuditCheck
from .osinfo import OSInfo
from .rpm_inventory import RpmInventory

REGISTRY = [OSInfo, RpmInventory]
