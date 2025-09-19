"""Compression and hashing utilities for Auditron data processing.

Provides gzip compression and SHA-256 hashing functions for
efficient storage and deduplication of audit data.
"""
import gzip
import hashlib


def sha256_bytes(b: bytes) -> str:
    """Calculate SHA-256 hash of bytes.
    
    Args:
        b: Raw bytes to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(b).hexdigest()


def gz_bytes(b: bytes) -> bytes:
    """Compress bytes using gzip compression.
    
    Args:
        b: Raw bytes to compress
        
    Returns:
        Gzip-compressed bytes
    """
    return gzip.compress(b, compresslevel=6)
