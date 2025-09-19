"""Base classes and interfaces for Auditron audit strategies.

Defines the core AuditContext and AuditCheck abstractions that all
audit strategies must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class AuditContext:
    """Execution context passed to audit strategies.
    
    Provides access to host configuration, SSH client, database connection,
    and other resources needed for audit strategy execution.
    """
    def __init__(
        self,
        host: dict,
        ssh: Any,
        db: Any,
        limits: dict,
        clock: Any,
        session_id: Optional[int] = None,
    ):
        """Initialize audit context.
        
        Args:
            host: Host configuration dictionary
            ssh: SSH client for remote command execution
            db: Database connection for storing results
            limits: Resource limits and configuration
            clock: Time source (for testing/mocking)
            session_id: Current audit session identifier
        """
        self.host = host
        self.ssh = ssh
        self.db = db
        self.limits = limits
        self.clock = clock
        self.session_id = session_id


class AuditCheck(ABC):
    """Abstract base class for all audit strategies.
    
    Defines the interface that all audit strategies must implement,
    including tool requirements and execution methods.
    """
    name: str = "base"
    requires: tuple[str, ...] = ()

    def probe(self, ctx: "AuditContext") -> bool:
        """Check if required tools are available on target host.
        
        Args:
            ctx: Audit execution context
            
        Returns:
            True if strategy can execute, False otherwise
        """
        # Default implementation always returns True
        # Subclasses should override to check for required tools
        return True

    @abstractmethod
    def run(self, ctx: "AuditContext") -> None:
        """Execute the audit strategy.
        
        Args:
            ctx: Audit execution context with host, SSH, and database access
        """
        ...
