REGISTRY = []

def register(cls):
    REGISTRY.append(cls)
    return cls
