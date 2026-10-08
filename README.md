<div align="center">

# 🔐 QRShield

### A Multi-Layer Framework for Secure QR Code Detection and Malicious URL Classification

**Deep tamper detection · Malicious-URL classification · TLS validation · ECDSA signature verification**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python\&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit\&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-EfficientNetB0-FF6F00?logo=tensorflow)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Random%20Forest-F7931E?logo=scikitlearn)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## Table of Contents

* [Why QRShield](#why-qrshield)
* [How it works](#how-it-works)
* [Key results](#key-results)
* [Repository structure](#repository-structure)
* [Installation](#installation)
* [Download the trained models and datasets](#download-the-trained-models-and-datasets)
* [Running the app](#running-the-app)
* [Generating signed QR codes](#generating-signed-qr-codes)
* [Reproducing the experiments](#reproducing-the-experiments)
* [Security notice](#security-notice)
* [Limitations](#limitations)
* [Citation](#citation)
* [Authors](#authors)
* [License](#license)

---

## Why QRShield

A QR code hides its destination behind a pattern the human eye cannot read, making it an effective delivery mechanism for quishing, malicious URLs, malware links, and physical tampering attacks.

QRShield treats QR security as a sequence of independent security checks rather than a single classification task.

The framework combines four complementary layers:

* **Layer 1:** Visual tamper detection
* **Layer 2:** Malicious URL classification
* **Layer 3:** TLS certificate validation
* **Layer 4:** Digital signature verification

The system operates in two modes:

* **Security-scanning mode:** A fail-fast cascade of image tamper detection, URL classification, and TLS validation.
* **Signature-verification mode:** An independent cryptographic verification path for issuer-signed QR codes.

---

## How it works

| Layer | Mode      | Purpose                                  | Technique                                         |
| ----: | :-------- | :--------------------------------------- | :------------------------------------------------ |
| **1** | Security  | Detect visual tampering of the QR image  | EfficientNetB0 transfer learning                  |
| **2** | Security  | Classify the decoded URL                 | Random Forest using 21 lexical features           |
| **3** | Security  | Validate the destination TLS connection  | SSL certificate, validity period, hostname checks |
| **4** | Signature | Verify issuer authenticity and integrity | ECDSA with NIST P-256 and SHA-256                 |

### Fail-Fast Pipeline

Layer 1 runs first because it is local and requires no network request.

Layer 2 analyzes the decoded URL using lexical features without external network lookup.

Layer 3 performs the network-dependent TLS validation only after the previous checks pass.

### Signed QR Payload

Signed QR codes contain a compact JSON payload:

```json
{"d": "https://example.org", "s": "<base64-encoded ECDSA signature>"}
```

The scanner automatically identifies whether the QR code contains a plain URL or a signed payload.

---

## Key Results

### Layer 1: QR Tamper Detection

The tamper detector uses a balanced synthetic dataset of **36,000 images** covering two tamper families:

* Module corruption
* Patch overlay

| Evaluation              | Accuracy   |
| :---------------------- | :--------- |
| Synthetic hold-out test | **100.0%** |
| Camera-like degradation | **84.9%**  |
| Unseen tamper types     | **51.7%**  |

The 100% result represents an in-distribution evaluation. External validation demonstrates that real-world generalization remains a limitation.

### Layer 2: Malicious URL Classification

The URL classifier was evaluated on a public corpus containing **651,191 URLs**.

| Model                  | Stratified Accuracy | Domain-Disjoint Accuracy |
| :--------------------- | :------------------ | :----------------------- |
| **Random Forest**      | **96.77%**          | 93.68%                   |
| XGBoost                | 96.74%              | **94.51%**               |
| Multi-Layer Perceptron | 95.63%              | 94.16%                   |
| Logistic Regression    | 80.24%              | 79.51%                   |

The URL classes include:

* Benign
* Defacement
* Malware
* Phishing

The prototype retains Random Forest because of its competitive performance and low inference cost.

### Layers 3 and 4

TLS validation and ECDSA signature verification were validated using functional accept/reject test cases covering certificate and signature conditions.

---

## Repository Structure

```text
QRShield/
├── app.py
├── scanner.py
├── signature_scanner.py
├── utils.py
├── tls_utils.py
├── crypto_utils.py
├── qr_generator.py
├── generate_keys.py
├── requirements.txt
│
├── Models/
├── Tempered_Model/
│   └── generate_tamper_dataset.py
└── URL_MODEL/
```

The trained model files are not stored directly in the repository because of their size.

---

## Installation

```bash
git clone https://github.com/Memona-hafeez/QRShield.git
cd QRShield

python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Required Packages

```text
streamlit
opencv-python
numpy
tensorflow
scikit-learn
joblib
cryptography
qrcode[pil]
Pillow
requests
python-dotenv
```

---

## Download the Trained Models and Datasets

| Asset                    | Source       | Location                            |
| :----------------------- | :----------- | :---------------------------------- |
| URL classifier           | Google Drive | `models/random_forest_model.joblib` |
| Tamper dataset and model | Google Drive | `models/qr_model.h5`                |
| URL training corpus      | Kaggle       | Used for retraining                 |

After downloading the models:

```text
models/
├── qr_model.h5
└── random_forest_model.joblib
```

---

## Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application provides two modes:

### Security Scanner

The QR code passes through:

```text
Tamper Detection
       ↓
URL Classification
       ↓
TLS Validation
       ↓
SAFE / BLOCKED
```

### Signature Scanner

The signature scanner verifies an issuer-signed QR code using the trusted public key.

A command-line webcam scanner is also available:

```bash
python scanner.py
```

---

## Generating Signed QR Codes

Generate an ECDSA P-256 key pair:

```bash
python generate_keys.py
```

Then edit the URL in `qr_generator.py` and generate a signed QR code:

```bash
python qr_generator.py
```

The generated QR code is saved as:

```text
secure_qr.png
```

The private signing key must remain secret.

---

## Reproducing the Experiments

| Notebook                                                   | Description                                 |
| :--------------------------------------------------------- | :------------------------------------------ |
| `Tempered_Model/generate_tamper_dataset.py`                | Generates the synthetic tamper dataset      |
| `Tempered_Model/Tempered_images_mmodel (3).ipynb`          | EfficientNetB0 training and evaluation      |
| `Tempered_Model/model extra validation.py.ipynb`           | External robustness evaluation              |
| `URL_MODEL/Copy_of_qr_payload_analysis_newwwwww (3).ipynb` | URL feature extraction and model comparison |

The experiment CSV files contain the results reported in the associated research work.

---

## Security Notice

This project is a **research prototype** and should not be deployed directly in production without additional security review.

### Private Key Protection

The private ECDSA key must never be committed to a public repository.

Add the following to `.gitignore`:

```text
ec_private.pem
.env
```

If a private key has already been committed, remove it from the repository history and generate a new key pair.

### TLS Limitation

A valid TLS certificate confirms that the connection is encrypted and associated with the hostname. It does **not** prove that the website itself is benign.

Therefore, TLS validation complements URL classification rather than replacing it.

---

## Limitations

* The tamper detector uses synthetic images from two manipulation families.
* Performance decreases under camera-like degradation and unseen tamper types.
* The current dataset does not include a large-scale real-world camera-captured tampering dataset.
* The URL dataset contains approximately 1.55% exact duplicate rows.
* Lexical URL models are vulnerable to concept drift.
* TLS and ECDSA layers were validated through functional test cases rather than field-scale deployment.
* End-to-end latency and combined-attack evaluation remain future work.

---

## Citation

If you use QRShield in your research, please cite:

```bibtex
@article{hafeez2026qrshield,
  title   = {QRShield: A Multi-Layer Framework for Secure QR Code Detection and Malicious URL Classification},
  author  = {Hafeez, Memona and Abdulhaq, Nimra},
  year    = {2026},
  note    = {Manuscript. Dept. of Data Science and Artificial Intelligence,
             Khwaja Fareed University of Engineering and Information Technology (KFUEIT)}
}
```

---

## Authors

* **Memona Hafeez**
* **Nimra Abdulhaq**

Department of Data Science and Artificial Intelligence
Khwaja Fareed University of Engineering and Information Technology (KFUEIT)

---

## License

Released under the **MIT License**.

The Malicious URLs dataset is used under its original Kaggle license. The EfficientNetB0 backbone is used under its respective license.
