import gzip, hashlib
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
def gz_bytes(b: bytes) -> bytes:
    return gzip.compress(b, compresslevel=6)
