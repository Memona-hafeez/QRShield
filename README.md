<div align="center">

# 🔐 QRShield

### A Multi-Layer Framework for Secure QR Code Detection and Malicious URL Classification

**Deep tamper detection · Malicious-URL classification · TLS validation · ECDSA signature verification**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python\&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit\&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-EfficientNetB0-FF6F00?logo=tensorflow\&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Random%20Forest-F7931E?logo=scikitlearn\&logoColor=white)
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

A QR code hides its destination behind a pattern the human eye cannot read, which makes it an ideal delivery vehicle for **quishing** (QR-code phishing), malware links, and physical sticker-overlay attacks. Most existing tools inspect only the decoded URL, so they miss a code that has been physically tampered with, say nothing about whether the destination server is trustworthy, and cannot prove who issued the code.

**QRShield treats QR security as a sequence of independent checks rather than a single classification.** It combines four complementary layers behind one scanner and runs them in two modes:

* **Security-scanning mode** — a *fail-fast* cascade of three checks (image tamper detection → URL classification → TLS validation). The first layer to reject a code stops the pipeline, so a visibly tampered code is blocked before any network request leaves the device.
* **Signature-verification mode** — an independent path that cryptographically verifies an issuer-signed code, for high-assurance use cases such as official documents and payments.

---

## How it works

| Layer | Mode      | Purpose                                                       | Technique                                                                               |
| ----: | :-------- | :------------------------------------------------------------ | :-------------------------------------------------------------------------------------- |
| **1** | Security  | Detect visual tampering of the QR image                       | EfficientNetB0 (transfer learning), 224×224 input, sigmoid head                         |
| **2** | Security  | Classify the decoded URL                                      | Random Forest over **21 lexical features** → *benign / defacement / malware / phishing* |
| **3** | Security  | Verify the destination is reached over a valid TLS channel    | `ssl` certificate chain + validity-period + hostname (SAN/wildcard-aware) check         |
| **4** | Signature | Prove the code was issued by a trusted party and is unaltered | **ECDSA over NIST P-256 (SECP256R1)** with SHA-256                                      |

**Fail-fast order.** Layer 1 runs first because it is local and needs no network. Layer 2 (pure string features, no network lookup) runs next. Layer 3, the only network-dependent layer, runs last, so the common case stays fast.

**Signed-QR payload format.** Signed codes carry a compact JSON object containing the data and its base64 signature:

```json
{"d": "https://example.org", "s": "<base64-encoded ECDSA signature>"}
```

The scanner automatically detects whether a code is a plain URL or a signed JSON payload and routes it accordingly.

---

## Key results

All numbers below are reproducible from the notebooks in this repository and are reported in the accompanying paper.

**Layer 1 — Tamper detector (EfficientNetB0)** · balanced synthetic dataset of **36,000** images (two tamper families: *module corruption*, *patch overlay*)

| Evaluation                                              | Accuracy                               |
| :------------------------------------------------------ | :------------------------------------- |
| Synthetic hold-out test (6,000 images, in-distribution) | **100.0%** (95% CI lower bound 99.94%) |
| External robustness — combined camera-like degradation  | 84.9%                                  |
| External robustness — **unseen** tamper types           | 51.7%                                  |

> The 100% figure is an **in-distribution upper bound only.** The external robustness check shows the detector does not yet generalize to real-world capture conditions or new tamper types.

**Layer 2 — URL classifier** · public corpus of **651,191** URLs

| Model                                   | Stratified acc. | Domain-disjoint acc. |
| :-------------------------------------- | :-------------- | :------------------- |
| **Random Forest** (300 trees, balanced) | **96.77%**      | 93.68%               |
| XGBoost                                 | 96.74%          | **94.51%**           |
| Multi-Layer Perceptron                  | 95.63%          | 94.16%               |
| Logistic Regression                     | 80.24%          | 79.51%               |

> On previously **unseen registrable domains**, XGBoost and the MLP significantly outperform the Random Forest (McNemar's test, p < 10⁻¹⁸). The Random Forest is retained in the prototype for its stratified-split tie and low inference cost.

**Layers 3 & 4** — validated with functional accept/reject test cases (valid / missing / expired / hostname-mismatch certificates; valid / absent / altered signatures).

---

## Repository structure

```text
QRShield/
├── app.py                     # Streamlit dual-mode scanner (main UI)
├── scanner.py                 # Webcam security-scan pipeline (Layers 1–3)
├── signature_scanner.py       # Signature-verification mode (Layer 4)
├── utils.py                   # preprocess_qr_image(), extract_url_features() [21 features]
├── tls_utils.py               # check_tls_certificate() — Layer 3
├── crypto_utils.py            # verify_signature() — Layer 4 (ECDSA/P-256)
├── qr_generator.py            # Create a signed QR code from a URL
├── generate_keys.py           # Generate an ECDSA P-256 key pair
├── requirements.txt           # Python dependencies
│
├── Models/                    # Original tamper + URL training notebooks
├── Tempered_Model/            # Tamper-dataset generator, training & external-validation notebooks
│   └── generate_tamper_dataset.py
└── URL_MODEL/                 # URL experiment artifacts (split indices, McNemar + Table IV CSVs, predictions)
```

> **Not stored in the repo** (too large): the trained model files `models/qr_model.h5` (tamper) and `models/random_forest_model.joblib` (URL), and the full image dataset. Download them from the links below and place them under a `models/` folder.

---

## Installation

```bash
# 1. Clone
git clone https://github.com/Memona-hafeez/SecureQRApp.git
cd SecureQRApp

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

**Important:** After renaming the GitHub repository, GitHub normally redirects the old repository URL. You can also update the clone URL above to the new repository URL once the rename is complete.

### `requirements.txt`

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

## Download the trained models and datasets

| Asset                                         | Link                                                                                               | Place it at                         |
| :-------------------------------------------- | :------------------------------------------------------------------------------------------------- | :---------------------------------- |
| URL classifier (`random_forest_model.joblib`) | [Google Drive](https://drive.google.com/file/d/1fhjFC2VzZP9fkGUleonPU7PpwAdU-8Z7)                  | `models/random_forest_model.joblib` |
| Tamper dataset + tamper model (`qr_model.h5`) | [Google Drive folder](https://drive.google.com/drive/folders/1YsJm8uNtD5JdIksJbSFxhqk2Br0nR_01)    | `models/qr_model.h5`                |
| URL training corpus (651,191 URLs)            | [Kaggle: Malicious URLs dataset](https://www.kaggle.com/datasets/sid321axn/malicious-urls-dataset) | used only for retraining            |

After downloading, your folder should contain:

```text
models/
├── qr_model.h5
└── random_forest_model.joblib
```

---

## Running the app

```bash
streamlit run app.py
```

This launches the dual-mode web interface:

* **Security Scanner** — upload or scan a QR code; it is passed through tamper detection → URL classification → TLS validation, and the verdict (SAFE / BLOCKED) is shown with the reason from the layer that decided.
* **Signature Scanner** — verify an issuer-signed QR code against the trusted public key (`ec_public.pem`).

A command-line webcam scanner is also available:

```bash
python scanner.py        # press Q to quit
```

---

## Generating signed QR codes

```bash
# 1. Generate an ECDSA P-256 key pair
python generate_keys.py

# 2. Edit the `url` value in qr_generator.py, then create a signed QR
python qr_generator.py
```

Keep `ec_private.pem` **secret**. Only `ec_public.pem` is used by the scanner to verify signatures.

---

## Reproducing the experiments

| Notebook                                                   | What it reproduces                                                                                                     |
| :--------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| `Tempered_Model/generate_tamper_dataset.py`                | Builds the 36,000-image synthetic tamper dataset                                                                       |
| `Tempered_Model/Tempered_images_mmodel (3).ipynb`          | Trains EfficientNetB0; 6,000-image test, confusion matrix, Grad-CAM                                                    |
| `Tempered_Model/model extra validation.py.ipynb`           | External robustness check (perturbations + unseen tamper types) → 84.9% / 51.7%                                        |
| `URL_MODEL/Copy_of_qr_payload_analysis_newwwwww (3).ipynb` | 21-feature extraction, RF + XGBoost + MLP + LR on stratified & domain-disjoint splits, McNemar's test, duplicate audit |

The CSVs in `URL_MODEL/` (`secureqr_model_comparison.csv`, `secureqr_mcnemar_domain_disjoint.csv`, `secureqr_table_iv_percent.csv`) contain the exact figures reported in the paper.

---

## Security notice

This is a research prototype. Two items **must** be fixed before real deployment:

1. **Remove the committed private key.** A published private key lets anyone forge "authentic" signatures, which defeats Layer 4 entirely. Delete it from the repo and its git history, then regenerate a fresh key pair:

```bash
git rm --cached ec_private.pem
echo "ec_private.pem" >> .gitignore
echo ".env" >> .gitignore
python generate_keys.py
```

2. **Do not commit `.env`.** Add it to `.gitignore` so API keys and secrets stay out of version control.

Also note: a valid TLS certificate proves the connection is encrypted, **not** that the site is benign. Phishing sites can hold valid certificates. Layer 3 complements, but does not replace, Layer 2.

---

## Limitations

* The tamper detector is trained and tested on **synthetic** images from two manipulation families.
* Its 100% score is in-distribution only.
* Accuracy drops to 84.9% under camera-like degradation and 51.7% on unseen tamper types.
* It will not catch a clean substitute code that carries no visual artefact.
* No real camera-captured dataset has been collected yet.
* The URL corpus contains approximately 1.55% exact-duplicate rows.
* Lexical models are subject to concept drift.
* TLS and ECDSA layers are validated with functional cases, not a field-scale study.
* End-to-end latency and a combined-attack evaluation of the full cascade are future work.

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

* **Memona Hafeez** — Department of Data Science and Artificial Intelligence, KFUEIT, Rahim Yar Khan, Pakistan · ORCID [0009-0007-4258-2386](https://orcid.org/0009-0007-4258-2386)
* **Nimra Abdulhaq** — Department of Data Science and Artificial Intelligence, KFUEIT, Rahim Yar Khan, Pakistan · ORCID [0009-0007-1327-6590](https://orcid.org/0009-0007-1327-6590)

---

## License

Released under the **MIT License**. The Malicious URLs dataset is used under its original Kaggle license; the EfficientNetB0 backbone is used under its respective license.
