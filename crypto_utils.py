import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

def load_public_key():
    with open("ec_public.pem", "rb") as f:
        return serialization.load_pem_public_key(f.read())

def verify_signature(data, signature):
    public_key = load_public_key()
    try:
        public_key.verify(
            base64.b64decode(signature),
            data.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except Exception as e:
        print("Verification error:", e)
        return False