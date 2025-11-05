import base64
from types import MappingProxyType
import uuid
import bcrypt
import random

def hash_pwd(plaintext: bytes) -> bytes:
    return bcrypt.hashpw(plaintext, bcrypt.gensalt())

def check_pwd(plaintext: bytes, hash: bytes) -> bool:
    return bcrypt.checkpw(plaintext, hash)

def uuid_to_str(id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(id.bytes).decode()

def str_to_uuid(id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(bytes = base64.urlsafe_b64decode(id))
    except Exception:
        return None


def gen_targets(n: int) -> list[int]:
    if n <= 0: return []

    targets = [i for i in range(n)] 
    assigned = [i for i in range(n)] 
    ptr = 0

    for i in range(n - 1):
        target_index = random.randint(1, n-i-1)
        target = targets[target_index]
        targets[target_index] = targets[-i-1]
            
        assigned[ptr] = target
        ptr = target

    assigned[ptr] = 0
    return assigned

def gen_target_maps(ids: list[int]) -> list[tuple[int, int]]:
    mapping = gen_targets(len(ids))

    mapped = []

    for i in range(len(mapping)):
        mapped.append((ids[i], ids[mapping[i]]))

    return mapped

