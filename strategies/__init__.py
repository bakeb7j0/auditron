"""
Audit strategies registry (incremental).
"""
from .base import AuditCheck
from .osinfo import OSInfo

REGISTRY = [OSInfo]
