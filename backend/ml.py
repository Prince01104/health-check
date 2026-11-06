"""Model registry, photo-quality check, prediction and Grad-CAM.

Models are looked up in models/ (or HC_MODELS_DIR). A check whose model file is
missing is reported as "not ready" and the app shows "coming soon" for it.
"""
import json
import os
import threading
import zipfile
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
MODELS_DIR = Path(os.environ.get("HC_MODELS_DIR", BASE / "models"))
REGISTRY = json.loads((MODELS_DIR / "registry.json").read_text(encoding="utf-8")) \
    if (MODELS_DIR / "registry.json").exists() \
    else json.loads((BASE / "models" / "registry.json").read_text(encoding="utf-8"))

CHECKS = ["oral", "skin", "infection", "nail"]
INVALID_PREFIX = "not_"          # classes like not_oral / not_skin mean "wrong kind of photo"

_cache = {}
_lock = threading.Lock()


def _paths(check):
    cfg = REGISTRY[check]
    return MODELS_DIR / cfg["model"], MODELS_DIR / cfg["classes"]


def is_ready(check: str) -> bool:
    m, c = _paths(check)
    return m.exists() and c.exists()


def pretty(label: str) -> str:
    return label.replace("_", " ").strip().title()


def classes_of(check: str):
    _, c = _paths(check)
    return json.loads(c.read_text(encoding="utf-8")) if c.exists() else []


_name_cache = {}


def model_name(check: str) -> str:
    """Name stored inside the .keras file (read without loading TensorFlow)."""
    m, _ = _paths(check)
    if not m.exists():
        return ""
    key = (str(m), m.stat().st_mtime)
    if key not in _name_cache:
        try:
            with zipfile.ZipFile(m) as z:
                _name_cache[key] = json.loads(z.read("config.json")).get("config", {}).get("name", "") or ""
        except Exception:
            _name_cache[key] = ""
    return _name_cache[key]


def is_dummy(check: str) -> bool:
    """True for the random demo models made by tools/make_dummy_models.py."""
    return model_name(check).startswith("dummy_")


def _load(check: str):
    """Load (and cache) the model for a check."""
    with _lock:
        if check in _cache:
            return _cache[check]
        import tensorflow as tf  # imported lazily: slow

        mpath, cpath = _paths(check)
        model = tf.keras.models.load_model(mpath, compile=False)
        classes = json.loads(cpath.read_text(encoding="utf-8"))
        h, w = model.input_shape[1:3]
        _cache[check] = {"model": model, "classes": classes, "size": (int(w), int(h))}
        return _cache[check]


def warm_up():
    for c in CHECKS:
        if is_ready(c):
            try:
                _load(c)
            except Exception as e:  # keep server alive even if one model is broken
                print(f"[warn] could not load {c}: {e}")


# ----------------------------------------------------------------- quality
def quality_check(img: Image.Image) -> dict:
    """Cheap, non-ML checks: size, blur, brightness."""
    arr = np.asarray(img.convert("RGB"))
    h, w = arr.shape[:2]
    scale = 320 / max(h, w)
    small = cv2.resize(arr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    bright = float(gray.mean())
    warnings = []
    if min(h, w) < 200:
        warnings.append("low_res")
    if blur < 40:
        warnings.append("blurry")
    if bright < 50:
        warnings.append("dark")
    elif bright > 220:
        warnings.append("bright")
    return {"ok": not warnings, "warnings": warnings, "blur": round(blur, 1),
            "brightness": round(bright, 1), "width": w, "height": h}


# ----------------------------------------------------------------- predict
def _prepare(img: Image.Image, size, interpolation: str):
    method = Image.NEAREST if interpolation == "nearest" else Image.BILINEAR
    x = np.asarray(img.convert("RGB").resize(size, method), dtype=np.float32) / 255.0
    return x[None, ...]


def _last_conv_name(model):
    import tensorflow as tf
    names = [l.name for l in model.layers if isinstance(l, tf.keras.layers.Conv2D)]
    return names[-1] if names else None


def _gradcam(model, x, class_idx, n_out):
    """Return a 0..1 heatmap (h' x w') or None if it cannot be computed."""
    import tensorflow as tf
    conv_name = _last_conv_name(model)
    if conv_name is None:
        return None
    try:
        xt = tf.convert_to_tensor(x)
        with tf.GradientTape() as tape:
            if isinstance(model, tf.keras.Sequential):
                h = xt
                conv = None
                for layer in model.layers:
                    h = layer(h, training=False)
                    if layer.name == conv_name:
                        conv = h
                        tape.watch(conv)
                out = h
            else:
                gm = tf.keras.Model(model.inputs, [model.get_layer(conv_name).output, model.output])
                conv, out = gm(xt, training=False)
                tape.watch(conv)
            if n_out == 1:
                score = out[:, 0] if class_idx == 1 else 1.0 - out[:, 0]
            else:
                score = out[:, class_idx]
        grads = tape.gradient(score, conv)
        w = tf.reduce_mean(grads, axis=(0, 1, 2))
        cam = tf.nn.relu(tf.reduce_sum(conv[0] * w, axis=-1)).numpy()
        m = cam.max()
        return cam / m if m > 1e-8 else None
    except Exception as e:
        print("[warn] gradcam failed:", e)
        return None


def overlay(img: Image.Image, cam, max_side=480):
    """Blend heatmap on the (resized) original. Returns (orig_rgb, blended_rgb) uint8 arrays."""
    w, h = img.size
    s = min(1.0, max_side / max(w, h))
    base = np.asarray(img.convert("RGB").resize((max(1, int(w * s)), max(1, int(h * s)))))
    if cam is None:
        return base, None
    heat = cv2.resize(cam.astype(np.float32), (base.shape[1], base.shape[0]), interpolation=cv2.INTER_CUBIC)
    heat = np.clip(heat, 0, 1)
    colored = cv2.applyColorMap((heat * 255).astype(np.uint8), cv2.COLORMAP_JET)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(base, 0.55, colored, 0.45, 0)
    return base, blended


def predict(check: str, img: Image.Image):
    entry = _load(check)
    model, classes, size = entry["model"], entry["classes"], entry["size"]
    cfg = REGISTRY[check]
    x = _prepare(img, size, cfg.get("interpolation", "nearest"))
    with _lock:
        out = model.predict(x, verbose=0)[0]
        n_out = out.shape[-1]
        if n_out == 1:                          # sigmoid / binary model
            probs = np.array([1.0 - out[0], out[0]], dtype=np.float32)
        else:
            probs = out.astype(np.float32)
        idx = int(np.argmax(probs))
        cam = _gradcam(model, x, idx, n_out)

    label = classes[idx]
    conf = float(probs[idx])
    thr = float(cfg.get("class_thresholds", {}).get(label, cfg.get("threshold", 0.7)))
    if label.lower().startswith(INVALID_PREFIX):
        status = "invalid"
    elif conf < thr:
        status = "uncertain"
    else:
        status = "ok"
    ranked = sorted(zip(classes, probs.tolist()), key=lambda t: -t[1])
    return {
        "label": label,
        "confidence": conf,
        "status": status,
        "threshold": thr,
        "probs": [{"label": l, "p": round(p, 4)} for l, p in ranked],
        "cam": cam,
    }
