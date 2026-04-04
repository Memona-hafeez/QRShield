from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# ECDSA key generate karo
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Private key save karo
with open("ec_private.pem", "wb") as f:
    f.write(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ))

# Public key save karo
with open("ec_public.pem", "wb") as f:
    f.write(public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("✅ ECDSA Keys generated!")
print("ec_private.pem — secret rakho")
print("ec_public.pem  — scanner mein use hogi")