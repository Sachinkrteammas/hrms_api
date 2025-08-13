# utils/encrypt.py
import hashlib
import base64
from typing import Union

def encrypt_slug(value: Union[str, int]) -> str:
    """
    Encrypt a value to create a slug for candidate verification
    """
    # Convert to string if it's an integer
    value_str = str(value)
    
    # Create a hash of the value
    hash_object = hashlib.sha256(value_str.encode())
    hash_hex = hash_object.hexdigest()
    
    # Take first 16 characters and encode to base64 for a shorter slug
    short_hash = hash_hex[:16]
    encoded = base64.urlsafe_b64encode(short_hash.encode()).decode()
    
    # Remove padding characters
    slug = encoded.rstrip('=')
    
    return slug 