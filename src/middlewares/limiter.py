from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter with in-memory storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)
