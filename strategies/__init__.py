"""
Audit strategies package.
Each module defines an AuditCheck subclass.
They are registered in REGISTRY for orchestration.
"""

# Import strategies here as they are implemented
from .base import AuditCheck

# Start with empty registry; will grow as we add components
REGISTRY: list[type[AuditCheck]] = []
