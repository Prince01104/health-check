"""Models, Profosa chat, feedback and sleep sounds. Edit this file when you add real backends.

The image models, Grad-CAM and photo-quality checks live in ml.py, the Gemini chat with its safety rules lives in
chat.py, and the result texts live in content.py. models/registry.json says which model file each check uses.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

import chat as gchat
import content
import ml
import news
import triage

Image.MAX_IMAGE_PIXELS = 40_000_000

BASE = Path(__file__).parent
SOUNDS_DIR = BASE / "assets" / "sounds"
DATA_DIR = Path(os.environ.get("HC_DATA_DIR", BASE / "data"))

# --------------------------------------------------------------- the four checks
# A check is live when it is listed in models/registry.json and its model files exist. Otherwise it says "coming soon".
CHECKS = {
    "skin": {"title": "Skin Check", "icon": ":material/face:", "blurb": "Face, rashes, spots", "doctor": "dermatologist",
             "hint": "Use a clear photo in daylight. No filters, no makeup."},
    "oral": {"title": "Oral Check", "icon": ":material/dentistry:", "blurb": "Teeth and gums", "doctor": "dentist",
             "hint": "Open wide and take the photo in good light."},
    "infection": {"title": "Infection Check", "icon": ":material/bug_report:", "blurb": "Wounds and spots",
                  "doctor": "doctor", "hint": "Keep the area in focus and well lit."},
    "nail": {"title": "Nail Check", "icon": ":material/back_hand:", "blurb": "Colour and shape", "doctor": "dermatologist",
             "hint": "Place the hand on a plain background."},
}
DOCTOR_SEARCH = {"dentist": "dentist", "dermatologist": "dermatologist", "doctor": "doctor"}

QUALITY_TEXT = {
    "low_res": "The photo is small. Move closer or use a higher quality photo.",
    "blurry": "The photo looks blurry. Hold the phone steady.",
    "dark": "The photo is too dark. Use more light.",
    "bright": "The photo is too bright. Avoid flash and glare.",
}


def model_ready(key: str) -> bool:
    return ml.is_ready(key)


def is_demo(key: str) -> bool:
    """True when the model file is only a random demo model (made by tools/make_dummy_models.py)."""
    return ml.is_dummy(key)


@st.cache_resource(show_spinner=False)
def load_models() -> bool:
    ml.warm_up()
    return True


def pretty(label: str) -> str:
    low = label.lower()
    if low.startswith("not_"):
        return "Photo not suitable"
    if "normal" in low:
        return "No clear problem"
    return ml.pretty(label)


def is_red_flag(label: str) -> bool:
    return gchat.is_urgent_label(label)


def info_for(key: str, label: str) -> dict:
    return content.describe(key, label)


def analyse(key: str, file) -> dict:
    """Photo in, result out. Phone photos are rotated by their EXIF tag first, as the camera app does."""
    img = Image.open(file)
    img.load()
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    quality = ml.quality_check(img)
    res = ml.predict(key, img)
    cam = res.pop("cam")
    # A photo that is blurry, small, too dark or too bright is never trusted as a confident result.
    demoted = res["status"] == "ok" and any(w in quality["warnings"] for w in ("blurry", "low_res", "dark", "bright"))
    if demoted:
        res["status"] = "uncertain"
    res["demoted"] = demoted
    base, heat = ml.overlay(img, cam)
    res.update(check=key, quality=quality, base=base, heat=heat, demo=is_demo(key), chat=[], feedback_done=False,
               ts=dt.datetime.now().isoformat(timespec="seconds"), time=dt.datetime.now().strftime("%d %b, %H:%M"),
               brightness=quality["brightness"], thumb=Image.fromarray(base).resize((160, max(1, int(160 * base.shape[0] / base.shape[1])))))
    return res


@st.cache_data(ttl=3600, show_spinner=False)
def health_news() -> list:
    """Today's headlines, cached for an hour so the feeds are not hit on every click. [] when no feed works."""
    return news.headlines(5)


def greeting() -> str:
    """Time-of-day greeting in Indian time (the server clock is UTC)."""
    hour = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).hour
    return "Hello," if hour < 5 else "Good morning," if hour < 12 else "Good afternoon," if hour < 17 else "Good evening,"


def daily_tip() -> str:
    tips = content.DAILY_TIPS
    return tips[dt.date.today().timetuple().tm_yday % len(tips)]["en"]


# --------------------------------------------------------------- progress, change and next step
ENTRY_KEYS = ("ts", "time", "check", "label", "confidence", "status", "probs", "emb", "brightness", "alert_lines", "next_step")
MAX_ENTRIES = 200


def risk_answers() -> dict:
    return st.session_state.get("risk", dict(triage.DEFAULT_RISK))


def quick_answers(check: str) -> dict:
    """The chips ticked on the check page for this check (this visit only)."""
    return st.session_state.get("quick", {}).get(check, {})


def risk_for(check: str) -> dict:
    return triage.risk_level(triage.merge_quick(risk_answers(), quick_answers(check)), check)


def see_doctor_if(check: str) -> list:
    return content.SEE_DOCTOR_IF.get(check, content.SEE_DOCTOR_IF["skin"])


def quality_of(file) -> dict:
    """Photo quality before the check (same steps as analyse), so the page can say 'sharp and well lit' early."""
    img = Image.open(file)
    img.load()
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    return ml.quality_check(img)


def record(res: dict, keep: bool = True) -> None:
    """Compare with the last check of the same type, decide the next step, and add the result to this visit's history.
    Only numbers and text are kept. The photo itself is not stored; a tiny thumbnail stays in memory for this visit."""
    hist = st.session_state.history
    same = [e for e in hist if e["check"] == res["check"]]
    prev = same[-1] if same else None
    res["change"] = triage.compare(prev, res, same[:-1])
    res["prev_thumb"] = prev.get("thumb") if prev else None
    res["risk"] = risk_for(res["check"])
    res["next"] = triage.escalate(res, res["risk"], res["change"], CHECKS[res["check"]]["doctor"], is_red_flag(res["label"]))
    if not keep:                       # the person did not tick "keep in my history"
        return
    entry = {k: res[k] for k in ("ts", "time", "check", "label", "confidence", "status", "probs", "emb", "brightness")}
    entry["alert_lines"] = res["change"]["lines"]
    entry["next_step"] = res["next"]["title"]
    entry["thumb"] = res.get("thumb")
    hist.append(entry)
    del hist[:-MAX_ENTRIES]


def export_progress() -> str:
    """The user's own progress file. Numbers only: no photos, no name, no email."""
    rows = [{k: e.get(k) for k in ENTRY_KEYS} for e in st.session_state.get("history", [])]
    return json.dumps({"app": "health-check", "version": 1, "risk": risk_answers(), "entries": rows}, separators=(",", ":"))


def import_progress(raw: bytes) -> tuple[bool, str]:
    """Load a progress file back in. Everything is validated, nothing in the file is ever run."""
    try:
        if len(raw) > 2_000_000:
            return False, "This file is too big."
        data = json.loads(raw.decode("utf-8"))
        if data.get("app") != "health-check" or data.get("version") != 1:
            return False, "This is not a Health Check progress file."
        rows = []
        for e in data["entries"][:MAX_ENTRIES]:
            if e["check"] not in CHECKS or e["status"] not in ("ok", "uncertain", "invalid"):
                continue
            dt.datetime.fromisoformat(e["ts"])
            probs = [{"label": str(p["label"])[:40], "p": float(p["p"])} for p in e["probs"][:12]]
            emb = e.get("emb")
            emb = [float(x) for x in emb][:256] if isinstance(emb, list) else None
            rows.append({"ts": e["ts"], "time": str(e.get("time", e["ts"]))[:20], "check": e["check"],
                         "label": str(e["label"])[:40], "confidence": float(e["confidence"]), "status": e["status"],
                         "probs": probs, "emb": emb, "brightness": float(e.get("brightness") or 0),
                         "alert_lines": [str(x)[:300] for x in (e.get("alert_lines") or [])][:6],
                         "next_step": str(e.get("next_step") or "")[:60], "thumb": None})
        risk = {k: (data["risk"].get(k) if data["risk"].get(k) in v else triage.DEFAULT_RISK[k])
                for k, v in triage.RISK_FIELDS.items()}
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeDecodeError):
        return False, "This file could not be read."
    hist = st.session_state.history
    have = {(e["ts"], e["check"]) for e in hist}
    hist.extend(r for r in rows if (r["ts"], r["check"]) not in have)
    hist.sort(key=lambda e: e["ts"])
    st.session_state.risk = risk
    return True, f"Loaded {len(rows)} earlier results."


def summary_for_doctor() -> str:
    risk = triage.risk_level(risk_answers())
    return triage.summary_text(st.session_state.get("name", ""), risk_answers(), risk,
                               st.session_state.get("history", []), dt.datetime.now().strftime("%d %b %Y, %H:%M"))


# --------------------------------------------------------------- Profosa chat (Gemini)
PERSONA = ("Your name in the app is Profosa, a friendly and calm health guide. "
           "Speak warmly, and keep it short.")
MAX_QUESTIONS = 15          # per result: keeps the free Gemini quota safe on a public demo
CHAT_ERRORS = {
    "not_configured": "Profosa's chat is off because no Gemini API key is set on this server. Your result above is still valid.",
    "busy": "Profosa is busy right now. Please try again in a minute. Your result above is still valid.",
    "timeout": "Profosa took too long to answer. Please try again. Your result above is still valid.",
    "unavailable": "Profosa could not reach Gemini right now. Please try again in a moment. Your result above is still valid.",
    "limit": "You have reached the question limit for this result. Please run a new check to ask more.",
}


def _secret(name: str):
    try:
        value = st.secrets.get(name)
    except Exception:  # no secrets file
        value = None
    return value or os.environ.get(name)


def gemini_available() -> bool:
    return bool(_secret("GEMINI_API_KEY"))


def ask_aira(res: dict, question: str) -> dict:
    """Ask Gemini about one result. Only TEXT is sent: the top predictions and the chat messages. Never the photo.
    Returns {"ok": bool, "reply": str | None, "error": str | None}. It never raises."""
    history = [{"role": "user" if role == "user" else "model", "text": text}
               for role, text in res["chat"] if role in ("user", "aira")]
    return gchat.ask(res["check"], res["label"], res["confidence"], res["status"], res["probs"], history, question,
                     doctor=CHECKS[res["check"]]["doctor"], api_key=_secret("GEMINI_API_KEY"), persona=PERSONA)


# --------------------------------------------------------------- feedback (saved to a CSV on the server)
def _append_csv(name: str, header: list, row: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow(header)
        writer.writerow(row)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def save_feedback(res: dict, helpful: str, comment: str) -> None:
    """Only the answer and an optional comment are saved. No photo, no name."""
    _append_csv("feedback.csv", ["time_utc", "check", "label", "confidence", "status", "helpful", "comment"],
                [_now(), res["check"], res["label"], round(res["confidence"], 3), res["status"], helpful,
                 comment.strip()[:500].replace("\n", " ")])


def feedback_form_url():
    return _secret("FEEDBACK_FORM_URL")


def admin_ok(given: str) -> bool:
    import hmac
    key = _secret("ADMIN_KEY")
    return bool(key) and hmac.compare_digest(str(given), str(key))


# --------------------------------------------------------------- sleep sounds
SOUNDS = [
    {"name": "Soft rain", "note": "Steady rain on leaves", "file": "rain.wav"},
    {"name": "Ocean at night", "note": "Slow waves, far away", "file": "ocean.wav"},
    {"name": "Deep hum", "note": "Low, warm, steady tones", "file": "hum.wav"},
    {"name": "Brown noise", "note": "Deep, smooth and calming", "file": "brown.wav"},
]


def sound_path(index: int) -> str:
    return str(SOUNDS_DIR / SOUNDS[index]["file"])
