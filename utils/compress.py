import gzip, hashlib, time

def sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def gz_bytes(b: bytes) -> bytes:
    return gzip.compress(b, compresslevel=6)
