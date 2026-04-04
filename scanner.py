import cv2
import numpy as np
import webbrowser
import json

from utils import preprocess_qr_image, extract_url_features
from tls_utils import check_tls_certificate

from keras.models import load_model
import joblib

image_model = load_model("models/qr_model.h5")
url_model = joblib.load("models/random_forest_model.joblib")

detector = cv2.QRCodeDetector()
cap = cv2.VideoCapture(0)

print("Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    data, bbox, _ = detector.detectAndDecode(frame)

    if data:
        signature = None

        # ---------- Try to parse JSON (optional) ----------
        try:
            qr_json = json.loads(data)
            qr_data = qr_json["data"]
            signature = qr_json.get("signature")
            print("✅ JSON QR detected")
        except:
            qr_data = data
            print("ℹ️ Plain QR detected (no signature)")

        if bbox is not None:
            bbox = np.int32(bbox)
            cv2.polylines(frame, [bbox], True, (0, 255, 0), 2)

            x = int(bbox[0][0][0])
            y = int(bbox[0][0][1])
            w = int(bbox[0][2][0] - bbox[0][0][0])
            h = int(bbox[0][2][1] - bbox[0][0][1])

            qr_image = frame[y:y+h, x:x+w]

            # ---------- Layer 1 ----------
            img_input = preprocess_qr_image(qr_image)
            img_pred = image_model.predict(img_input)
            img_label = np.argmax(img_pred)

            if img_label == 1:
                print("❌ Tampered QR detected (Image model)")
                continue
            else:
                print("✅ Layer 1 passed")

            # ---------- Layer 2 ----------
            url_features = extract_url_features(qr_data)
            url_pred = url_model.predict(url_features)

            if url_pred[0] == 1:
                print("❌ Malicious URL detected (ML model)")
                continue
            else:
                print("✅ Layer 2 passed")

            # ---------- Layer 3 ----------
            tls_valid, tls_msg = check_tls_certificate(qr_data)
            if not tls_valid:
                print(f"❌ TLS failed: {tls_msg}")
                continue
            else:
                print(f"✅ Layer 3 passed: {tls_msg}")

        

            # Open URL
            print("🔓 Opening URL:", qr_data)
            webbrowser.open(qr_data)

    cv2.imshow("Secure QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()