from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
import base64, json, qrcode

url = "https://botifyhub.io"

with open("ec_private.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

signature = private_key.sign(url.encode(), ec.ECDSA(hashes.SHA256()))
sig_b64 = base64.b64encode(signature).decode()

qr_string = json.dumps({"d": url, "s": sig_b64}, separators=(',', ':'))
print("QR length:", len(qr_string))

qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
qr.add_data(qr_string)
qr.make(fit=True)
print("Version:", qr.version)

qr.make_image(fill_color="black", back_color="white").save("secure_qr.png")
print("✅ Done!")