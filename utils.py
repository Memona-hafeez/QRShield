import cv2
import numpy as np
from urllib.parse import urlparse
import requests
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ---------------- Image Preprocessing ----------------
def preprocess_qr_image(qr_img):
    qr_img = cv2.resize(qr_img, (128, 128))
    qr_img = qr_img / 255.0
    qr_img = np.expand_dims(qr_img, axis=0)
    return qr_img


# ---------------- URL Feature Extraction ----------------
def extract_url_features(url):

    parsed = urlparse(url)
    hostname = parsed.hostname if parsed.hostname else ""
    path = parsed.path if parsed.path else ""

    features = [
        int(any(char.isdigit() for char in url)),
        int(url.startswith("https")),
        1 if 'google.com' in url else 0,
        url.count('.'),
        url.count('www'),
        url.count('@'),
        path.count('/'),
        0,
        1 if len(url) < 20 else 0,
        url.count('https'),
        url.count('http'),
        url.count('%'),
        url.count('?'),
        url.count('='),
        len(url),
        len(hostname),
        0,
        sum(c.isdigit() for c in url),
        sum(c.isalpha() for c in url),
        len(path.split('/')[-1]),
        len(hostname.split('.')[-1])
    ]

    return np.array(features).reshape(1, -1)


# ---------------- Google Web Risk Check ----------------
def check_google_webrisk(url):

    endpoint = "https://webrisk.googleapis.com/v1/uris:search"

    params = {
        "uri": url,
        "threatTypes": [
            "MALWARE",
            "SOCIAL_ENGINEERING",
            "UNWANTED_SOFTWARE"
        ],
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(endpoint, params=params, timeout=5)

        if response.status_code == 200:
            result = response.json()

            if "threat" in result:
                print("⚠ Google Threat Found:", result["threat"])
                return True
            else:
                return False

        else:
            print("Web Risk API error:", response.status_code)
            return False

    except requests.exceptions.RequestException as e:
        print("Web Risk Connection Error:", e)
        return False
