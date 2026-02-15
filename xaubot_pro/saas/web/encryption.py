"""AES-256-GCM encryption for MT5 credentials"""
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Generate key: base64.b64encode(os.urandom(32)).decode()
ENCRYPTION_KEY = os.environ.get('XAUBOT_ENC_KEY', base64.b64encode(os.urandom(32)).decode())

def _get_key():
    return base64.b64decode(ENCRYPTION_KEY)

def encrypt(plaintext: str) -> str:
    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.b64encode(nonce + ct).decode('utf-8')

def decrypt(encrypted: str) -> str:
    aesgcm = AESGCM(_get_key())
    data = base64.b64decode(encrypted)
    nonce, ct = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode('utf-8')
