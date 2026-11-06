"""Make tiny RANDOM demo models so the app runs before your real models are copied in.

    python tools/make_dummy_models.py            # writes into ./models
    python tools/make_dummy_models.py some_dir   # writes into some_dir

The models are named "dummy_<check>"; the app detects that and shows a
"demo model" warning. Copy your real model over the same file name and the
warning disappears by itself. Checks listed in SKIP get no model, so the app
shows them as "Coming soon".
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf  # noqa: E402

# check: (model file, classes file, input size, classes)
SPECS = {
    "oral": ("oral4_model.keras", "oral4_classes.json", 128,
             ["calculus", "gingivitis", "hypodontia", "mouth_ulcer"]),
    "skin": ("skin_model.keras", "skin_classes.json", 150,
             ["eczema", "tinea", "unknown_normal"]),
}


def build(check: str, size: int, n_classes: int):
    L = tf.keras.layers
    model = tf.keras.Sequential(
        [L.Input((size, size, 3)),
         L.Conv2D(8, 3, padding="same", activation="relu", name="conv1"),
         L.MaxPooling2D(),
         L.Conv2D(16, 3, padding="same", activation="relu", name="conv2"),
         L.GlobalAveragePooling2D(),
         L.Dense(n_classes, activation="softmax", name="out")],
        name=f"dummy_{check}",
    )
    k, b = model.get_layer("out").get_weights()
    model.get_layer("out").set_weights([k * 40.0, b])      # make outputs fairly confident
    return model


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    tf.keras.utils.set_random_seed(0)
    for check, (mfile, cfile, size, classes) in SPECS.items():
        build(check, size, len(classes)).save(out_dir / mfile)
        (out_dir / cfile).write_text(json.dumps(classes), encoding="utf-8")
        print("wrote", out_dir / mfile)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "models"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else base)
