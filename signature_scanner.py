import cv2
import json
import webbrowser
from crypto_utils import verify_signature

detector = cv2.QRCodeDetector()
cap = cv2.VideoCapture(0)

print("Scanner Running... Press Q to quit")

last_data = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    data, bbox, _ = detector.detectAndDecode(frame)

    if data and data != last_data:
        last_data = data
        print("\n--- QR Detected ---")
        try:
            qr_json = json.loads(data)
            qr_data = qr_json.get("d")
            signature = qr_json.get("s")

            print("Data:", qr_data)

            if signature:
                if verify_signature(qr_data, signature):
                    print("✅ Signature VALID — Opening link...")
                    webbrowser.open(qr_data)  # ← Browser mein khul jayegi
                else:
                    print("❌ Signature INVALID — Link blocked!")
                    # Fake/tampered QR — link nahi khulegi
            else:
                print("ℹ️ No signature found in QR")

        except json.JSONDecodeError:
            print("❌ Not a secure QR (expected JSON)")
            print("RAW DATA:", data)
        except Exception as e:
            print("Error:", e)

    cv2.imshow("Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()