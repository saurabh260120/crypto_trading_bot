"""
Security utilities: encryption, JWT, password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def get_encryption_key() -> bytes:
    """Derive encryption key from master key."""
    master_key = settings.TRADE_MASTER_KEY.encode()
    # Use PBKDF2 to derive a 32-byte key
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'trading_platform_salt',  # In production, use a random salt stored securely
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(master_key)
    return base64.urlsafe_b64encode(key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key using Fernet."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key."""
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode()


def sign_delta_request(api_secret: str, method: str, path: str, body: str = "", timestamp: str = "") -> str:
    """Sign a Delta Exchange API request."""
    import time
    if not timestamp:
        timestamp = str(int(time.time()))
    
    message = f"{timestamp}{method}{path}{body}"
    signature = hashlib.sha256(f"{api_secret}{message}".encode()).hexdigest()
    return signature

