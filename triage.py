"""Risk factors, change over time and the escalation pathway. Pure Python, no Streamlit, so it is easy to test.

What this file is and is not:
- It is a set of simple, readable rules. Every alert comes with the reason in plain words.
- It is NOT a clinical risk score and the change thresholds are NOT clinically validated. The CNN was not trained
  on photo pairs over time, so "change" here means: the model's answer moved, or the photo "fingerprint" moved.
- Nothing here gives a diagnosis. The highest level only says "see a doctor soon".
"""
from __future__ import annotations

import datetime as dt
import math

# ------------------------------------------------------------------ risk factors (all optional)
RISK_FIELDS = {
    "age": ["Prefer not to say", "Under 18", "18 to 39", "40 to 59", "60 or more"],
    "tobacco": ["Prefer not to say", "None", "Smoking", "Chewing (gutka, paan, tobacco)", "Both"],
    "alcohol": ["Prefer not to say", "No", "Yes"],
    "diabetes": ["Prefer not to say", "No", "Yes"],
    "family": ["Prefer not to say", "No", "Yes"],           # skin cancer or mouth cancer in the family
    "sun": ["Prefer not to say", "Low", "High (outdoor work, easy sunburn)"],
    "duration": ["Prefer not to say", "Less than 2 weeks", "2 to 4 weeks", "More than 4 weeks"],
    "changing": ["Prefer not to say", "No", "Yes"],         # growing, bleeding, or changing colour or shape
}
DEFAULT_RISK = {k: v[0] for k, v in RISK_FIELDS.items()}


def risk_level(answers: dict, check: str | None = None) -> dict:
    """Count simple, well-known risk factors. Returns {"level": low|moderate|high|unknown, "points", "reasons"}."""
    a = {**DEFAULT_RISK, **(answers or {})}
    if all(a[k] == DEFAULT_RISK[k] for k in a):
        return {"level": "unknown", "points": 0, "reasons": []}
    pts, why = 0, []

    def add(n, text):
        nonlocal pts
        pts += n
        why.append(text)

    if a["tobacco"] in ("Smoking", "Chewing (gutka, paan, tobacco)", "Both"):
        add(2 if check in (None, "oral") else 1, "Tobacco use")
    if a["alcohol"] == "Yes" and check in (None, "oral"):
        add(1, "Regular alcohol")
    if a["diabetes"] == "Yes":
        add(1, "Diabetes (slows healing, raises infection risk)")
    if a["family"] == "Yes":
        add(2, "Skin or mouth cancer in the family")
    if a["sun"].startswith("High") and check in (None, "skin"):
        add(1, "High sun exposure")
    if a["age"] == "60 or more":
        add(1, "Age 60 or more")
    if a["duration"] == "More than 4 weeks":
        add(2, "Problem lasting more than 4 weeks")
    elif a["duration"] == "2 to 4 weeks":
        add(1, "Problem lasting 2 to 4 weeks")
    if a["changing"] == "Yes":
        add(3, "Growing, bleeding or changing")
    level = "high" if (pts >= 4 or a["changing"] == "Yes") else "moderate" if pts >= 2 else "low"
    return {"level": level, "points": pts, "reasons": why}


# ------------------------------------------------------------------ change between two photos
# Prototype thresholds. Chosen to be cautious, not clinically validated.
TV_ALERT = 0.35          # how far the model's probabilities moved (0 = same, 1 = completely different)
EMB_ALERT = 0.25         # cosine distance between the two photo fingerprints
LIGHT_GAP = 45           # brightness gap (0 to 255) above which the two photos are hard to compare
PERSIST_DAYS = 14        # same mouth ulcer in checks 14 or more days apart


def _vec(probs):
    return {p["label"]: float(p["p"]) for p in probs}


def _tv(a, b):
    keys = set(a) | set(b)
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def _cos_dist(a, b):
    if not a or not b or len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return None
    return max(0.0, 1.0 - dot / (na * nb))


def _days(a, b):
    try:
        return abs((dt.datetime.fromisoformat(b) - dt.datetime.fromisoformat(a)).total_seconds()) / 86400
    except (TypeError, ValueError):
        return None


def _is_normal(label):
    return "normal" in str(label).lower()


def compare(prev: dict | None, cur: dict, earlier: list | None = None) -> dict:
    """Compare this check with the previous one of the same type. `earlier` = all older entries of that type."""
    out = {"has_prev": prev is not None, "alert": False, "lines": [], "tv": None, "emb": None, "days": None,
           "label_changed": False, "persisting": False}
    if prev is None:
        return out
    tv = _tv(_vec(prev["probs"]), _vec(cur["probs"]))
    emb = _cos_dist(prev.get("emb"), cur.get("emb"))
    days = _days(prev["ts"], cur["ts"])
    out.update(tv=round(tv, 3), emb=None if emb is None else round(emb, 3), days=days)
    both_ok = prev["status"] == "ok" and cur["status"] == "ok"
    lines = []
    if both_ok and prev["label"] != cur["label"]:
        out["label_changed"] = True
        lines.append(f"The result changed from {prev['label'].replace('_', ' ')} to {cur['label'].replace('_', ' ')}.")
    if tv >= TV_ALERT:
        lines.append(f"The AI's answer moved a lot between the two photos (change {tv:.2f} on a 0 to 1 scale).")
    if emb is not None and emb >= EMB_ALERT:
        lines.append(f"The two photos look quite different to the AI (difference {emb:.2f}).")
    light = abs(float(prev.get("brightness", 0)) - float(cur.get("brightness", 0)))
    if light > LIGHT_GAP:
        out["lighting_differs"] = True
        lines.append("The light is very different in the two photos, so this comparison is less reliable. "
                     "Retake both in the same light.")
    # Same mouth ulcer found again two or more weeks later
    if cur["check"] == "oral" and cur["label"] == "mouth_ulcer" and cur["status"] == "ok":
        first = None
        for e in sorted((earlier or []) + [prev], key=lambda e: e["ts"]):
            if e["label"] == "mouth_ulcer" and e["status"] == "ok":
                first = e
                break
        gap = _days(first["ts"], cur["ts"]) if first else None
        if gap is not None and gap >= PERSIST_DAYS:
            out["persisting"] = True
            lines.append(f"A mouth ulcer has been seen for about {int(gap)} days. A mouth ulcer that lasts more than "
                         "2 to 3 weeks should be looked at by a dentist or doctor.")
    # An alert needs a real signal, not only a lighting warning
    signal = out["label_changed"] or tv >= TV_ALERT or (emb is not None and emb >= EMB_ALERT) or out["persisting"]
    out["alert"] = bool(signal and not (out.get("lighting_differs") and not out["persisting"] and not out["label_changed"]))
    out["lines"] = lines
    return out


# ------------------------------------------------------------------ escalation pathway
LEVELS = {
    "retake": {"title": "Retake the photo", "color": "#B4531A",
               "text": "The AI could not give a reliable result from this photo."},
    "routine": {"title": "Nothing worrying seen", "color": "#0B6665",
                "text": "Keep an eye on it. Regular check-ups are still a good idea."},
    "watch": {"title": "Keep watching", "color": "#8A6A10",
              "text": "Check again in about 2 weeks with a new photo. See a doctor if it gets worse."},
    "doctor": {"title": "See a doctor soon", "color": "#B3261E",
               "text": "Please book a visit. This app cannot confirm what it is."},
}


def escalate(res: dict, risk: dict, change: dict, doctor: str = "doctor", urgent_label: bool = False) -> dict:
    """One clear next step. Order matters: the strictest rule that applies wins."""
    status, quality = res["status"], res.get("quality", {}).get("warnings", [])
    reasons: list[str] = []

    # 1. The photo is not good enough. No result is trusted, and the way forward is spelled out.
    if status == "invalid" or status == "uncertain" or any(w in quality for w in ("blurry", "low_res", "dark", "bright")):
        if status == "invalid":
            reasons.append("The photo does not look like the right body area.")
        if status == "uncertain":
            reasons.append("The AI is not confident about this photo.")
        for w in quality:
            reasons.append({"blurry": "The photo is blurry.", "low_res": "The photo is too small.",
                            "dark": "The photo is too dark.", "bright": "The photo is too bright."}.get(w, w))
        level = "retake"
        if risk["level"] == "high" or urgent_label or change.get("persisting"):
            level = "doctor"
            reasons.append("Your answers show higher risk, so do not wait for a better photo before seeing a doctor.")
        return _pack(level, reasons, doctor, retake_tip=True)

    # 2. A confident result.
    normal = _is_normal(res["label"])
    if urgent_label:
        reasons.append("This type of result always needs a doctor.")
    if change.get("persisting"):
        reasons.append("The problem has lasted 2 weeks or more.")
    if change.get("alert") and not normal:
        reasons.append("The result changed since your last check.")
    if risk["level"] == "high" and not normal:
        reasons.append("Your risk-factor answers are high: " + ", ".join(risk["reasons"][:3]) + ".")
    if reasons:
        return _pack("doctor", reasons, doctor)
    if not normal:
        if risk["level"] == "moderate":
            reasons.append("Some risk factors: " + ", ".join(risk["reasons"][:3]) + ".")
        reasons.append("The AI sees a possible problem but is not a diagnosis.")
        return _pack("watch", reasons, doctor)
    if change.get("alert"):
        return _pack("watch", ["The photo changed since your last check."], doctor)
    return _pack("routine", [], doctor)


def _pack(level, reasons, doctor, retake_tip=False):
    base = LEVELS[level]
    text = base["text"]
    if level == "retake":
        text += " Use daylight, hold the phone steady, and fill the frame with the area. If you still cannot get a clear photo, or you are worried, see a " + doctor + "."
    if level == "doctor":
        text = f"Please see a {doctor} soon. This app cannot confirm what it is."
    return {"level": level, "title": base["title"], "color": base["color"], "text": text, "reasons": reasons}


# ------------------------------------------------------------------ share with a specialist
def summary_text(name: str, risk_answers: dict, risk: dict, entries: list, generated: str) -> str:
    """A plain-text summary the user can hand to a doctor. No photos, no email, only what the user chose to enter."""
    L = ["HEALTH CHECK - SUMMARY FOR A DOCTOR", f"Created: {generated}", "",
         "IMPORTANT: This is output of an AI photo-screening aid. It is not a diagnosis. Please examine the patient.", ""]
    if name:
        L.append(f"Name given by the user: {name}")
    L.append("Risk factors given by the user (self-reported):")
    answered = {k: v for k, v in (risk_answers or {}).items() if v != DEFAULT_RISK.get(k)}
    L += [f"  - {k}: {v}" for k, v in answered.items()] or ["  - none given"]
    if risk["level"] != "unknown":
        L.append(f"Risk-factor level (simple count, not clinical): {risk['level']} - {', '.join(risk['reasons'])}")
    L += ["", "Photo checks (oldest first):"]
    for e in sorted(entries, key=lambda e: e["ts"]):
        top = ", ".join(f"{p['label']} {p['p'] * 100:.0f}%" for p in e["probs"][:3])
        L.append(f"  {e['time']} | {e['check']} | {e['status']} | best guess {e['label']} {e['confidence'] * 100:.0f}% | top: {top}")
        if e.get("alert_lines"):
            L += [f"      ALERT: {x}" for x in e["alert_lines"]]
        if e.get("next_step"):
            L.append(f"      App advice: {e['next_step']}")
    L += ["", "Photos are not included. The user holds the originals."]
    return "\n".join(L)
