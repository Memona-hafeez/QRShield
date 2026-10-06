"""
generate_tamper_dataset.py  --  RE-IMPLEMENTATION (see note)


Usage:
    pip install qrcode[pil] pillow numpy
    python generate_tamper_dataset.py --urls urls.csv --out qr_dataset_v2 \
        --n_train 15000 --n_test 3000 --seed 42
urls.csv: one column named 'url' with at least n_train + n_test unique URLs.
Train and test payloads are disjoint by construction.
Log columns: filename, category, meta
  patch_overlay      meta = (name, x, y, w, h)           pixels, w == h
  module_corruption  meta = (name, n_flipped, qr_version, box_px)
"""
import argparse, csv, os, random
import numpy as np
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image, ImageDraw

SIZE = 512

def make_qr(url, box_px=None):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=4, box_size=1)
    qr.add_data(url); qr.make(fit=True)
    m = np.array(qr.get_matrix(), dtype=np.uint8)          # 1 = dark module, includes border
    return qr.version, m

def render(matrix, box_px):
    img = np.where(matrix == 1, 0, 255).astype(np.uint8)
    img = np.kron(img, np.ones((box_px, box_px), dtype=np.uint8))
    im = Image.fromarray(img, "L").convert("RGB")
    return im.resize((SIZE, SIZE), Image.NEAREST)

def box_for(matrix):
    return max(1, SIZE // matrix.shape[0])

def module_corruption(matrix, rng):
    m = matrix.copy(); n = m.shape[0]
    k = rng.randint(3, 12)                                   # number of flipped data modules
    flipped = 0
    while flipped < k:
        r, c = rng.randrange(4, n - 4), rng.randrange(4, n - 4)
        if (r < 13 and c < 13) or (r < 13 and c > n - 14) or (r > n - 14 and c < 13):
            continue                                         # skip finder-pattern areas
        m[r, c] ^= 1; flipped += 1
    return m, k

def patch_overlay(im, rng):
    s = rng.randint(54, 98)
    x, y = rng.randint(60, SIZE - s - 60), rng.randint(60, SIZE - s - 60)
    d = ImageDraw.Draw(im)
    d.rectangle([x, y, x + s, y + s], fill=rng.choice([(0, 0, 0), (255, 255, 255), (128, 128, 128)]))
    return im, (x, y, s, s)

def build(urls, split, root, rng, log_rows):
    os.makedirs(f"{root}/real_qr_{split}", exist_ok=True)
    os.makedirs(f"{root}/fake_qr_{split}", exist_ok=True)
    tag = "" if split == "full" else "_test"
    for i, url in enumerate(urls):
        ver, m = make_qr(url); box = box_for(m)
        render(m, box).save(f"{root}/real_qr_{split}/real{tag}_{i:05d}.png")
        fname = f"fake{tag}_{i:05d}.png"
        if rng.random() < 0.5:
            m2, k = module_corruption(m, rng); im = render(m2, box)
            meta = ("module_corruption", k, ver, box); cat = "module_corruption"
        else:
            im, (x, y, w, h) = patch_overlay(render(m, box), rng)
            meta = ("patch_overlay", x, y, w, h); cat = "patch_overlay"
        im.save(f"{root}/fake_qr_{split}/{fname}")
        log_rows.append((fname, cat, str(meta)))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--n_train", type=int, default=15000); ap.add_argument("--n_test", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    urls = [r["url"] for r in csv.DictReader(open(a.urls))]
    urls = list(dict.fromkeys(urls)); rng.shuffle(urls)       # unique, shuffled
    assert len(urls) >= a.n_train + a.n_test, "need more unique URLs"
    train, test = urls[:a.n_train], urls[a.n_train:a.n_train + a.n_test]
    assert not set(train) & set(test)
    for split, u, logname in (("full", train, "tamper_log.csv"), ("test", test, "tamper_log_test.csv")):
        rows = []; build(u, split, a.out, rng, rows)
        with open(f"{a.out}/fake_qr_{split}/{logname}", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["filename", "category", "meta"]); w.writerows(rows)
    print("done")
