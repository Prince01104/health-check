"""Health Check API + web app.

Run from the project folder:   uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000  (phone on the same Wi-Fi: use --host 0.0.0.0).
"""
import datetime as dt
import io
import json
import re
import sqlite3
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel

from . import db, ml
from .content import DAILY_TIPS, describe
from .report import build_pdf

Image.MAX_IMAGE_PIXELS = 40_000_000
FRONT = Path(__file__).resolve().parent.parent / "frontend"
MAX_UPLOAD = 10 * 1024 * 1024
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CHECK_META = {
    "oral": {"title": "Oral Check", "subtitle": "Teeth and gums", "doctor": "dentist"},
    "skin": {"title": "Skin Check", "subtitle": "Face, acne and rashes", "doctor": "dermatologist"},
    "infection": {"title": "Infection Check", "subtitle": "Wounds and spots", "doctor": "doctor"},
    "nail": {"title": "Nail Check", "subtitle": "Colour and shape", "doctor": "dermatologist"},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    threading.Thread(target=ml.warm_up, daemon=True).start()   # load models in the background
    yield


app = FastAPI(title="Health Check", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(FRONT)), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


# ------------------------------------------------------------------ helpers
_attempts = defaultdict(deque)


def throttle(key: str, limit: int = 10, window: int = 300):
    """Very small in-memory rate limit for login / signup."""
    now = time.time()
    q = _attempts[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many attempts. Please wait a few minutes and try again.")
    q.append(now)


def current_user(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    user = db.user_for_token(token)
    if not user:
        raise HTTPException(401, "Please log in again.")
    user["_token"] = token
    return user


def display_label(label: str) -> str:
    low = label.lower()
    if low.startswith(ml.INVALID_PREFIX):
        return "Photo not suitable"
    if "normal" in low:
        return "No clear problem"
    return ml.pretty(label)


def own_row(hid: int, user: dict):
    with db.conn() as c:
        row = c.execute("SELECT * FROM history WHERE id=? AND user_id=?", (hid, user["id"])).fetchone()
    if not row:
        raise HTTPException(404, "Result not found.")
    return dict(row)


def payload(row: dict) -> dict:
    info = describe(row["check_type"], row["label"])
    probs = json.loads(row["probs"])
    for p in probs:
        p["display"] = display_label(p["label"])
    return {
        "id": row["id"],
        "check": row["check_type"],
        "label": row["label"],
        "display": display_label(row["label"]),
        "confidence": row["confidence"],
        "status": row["status"],
        "probs": probs,
        "quality": json.loads(row["quality"]),
        "has_heatmap": bool(row["has_heatmap"]),
        "created": row["created"],
        "see_doctor": info["see_doctor"],
        "content": {"en": info["en"], "hi": info["hi"]},
        "doctor": CHECK_META[row["check_type"]]["doctor"],
        "demo": ml.is_dummy(row["check_type"]),
    }


# --------------------------------------------------------------------- auth
class SignupIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/signup")
def signup(body: SignupIn, request: Request):
    throttle("signup:" + (request.client.host if request.client else "?"), limit=20)
    name = body.name.strip()[:60]
    email = body.email.strip().lower()
    if not name:
        raise HTTPException(400, "Please enter your name.")
    if not EMAIL_RE.match(email) or len(email) > 120:
        raise HTTPException(400, "Please enter a valid email.")
    if len(body.password) < 6 or len(body.password) > 128:
        raise HTTPException(400, "Password must be 6 to 128 characters.")
    pw_hash, salt = db.hash_pw(body.password)
    try:
        with db.conn() as c:
            cur = c.execute(
                "INSERT INTO users(name,email,pw_hash,salt,created) VALUES(?,?,?,?,?)",
                (name, email, pw_hash, salt, time.time()),
            )
            uid = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "This email is already registered. Please log in.")
    return {"token": db.new_token(uid), "user": {"name": name, "email": email}}


@app.post("/api/login")
def login(body: LoginIn):
    email = body.email.strip().lower()
    throttle("login:" + email)
    with db.conn() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not u:
        db.hash_pw(body.password)                      # keep timing similar
        raise HTTPException(401, "Wrong email or password.")
    if not db.check_pw(body.password, u["pw_hash"], u["salt"]):
        raise HTTPException(401, "Wrong email or password.")
    return {"token": db.new_token(u["id"]), "user": {"name": u["name"], "email": u["email"]}}


@app.post("/api/logout")
def logout(user=Depends(current_user)):
    db.delete_token(user["_token"])
    return {"ok": True}


def stats_for(user_id: int, tz_minutes: int) -> dict:
    with db.conn() as c:
        rows = c.execute("SELECT check_type, created FROM history WHERE user_id=?", (user_id,)).fetchall()
    by_check = defaultdict(int)
    days = set()
    shift = dt.timedelta(minutes=tz_minutes)
    for r in rows:
        by_check[r["check_type"]] += 1
        days.add((dt.datetime.fromtimestamp(r["created"], dt.timezone.utc) + shift).date())
    today = (dt.datetime.now(dt.timezone.utc) + shift).date()
    day = today if today in days else today - dt.timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= dt.timedelta(days=1)
    return {"total": len(rows), "by_check": dict(by_check), "streak": streak, "today_done": today in days}


@app.get("/api/me")
def me(tz: int = 0, user=Depends(current_user)):
    tz = max(-840, min(840, tz))
    return {"name": user["name"], "email": user["email"], "stats": stats_for(user["id"], tz)}


@app.delete("/api/me")
def delete_me(user=Depends(current_user)):
    with db.conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM history WHERE user_id=?", (user["id"],))]
    for hid in ids:
        db.remove_files_for(hid)
    with db.conn() as c:
        c.execute("DELETE FROM users WHERE id=?", (user["id"],))   # tokens + history cascade
    return {"ok": True}


# ------------------------------------------------------------------- checks
@app.get("/api/checks")
def checks():
    out = []
    for cid in ml.CHECKS:
        ready = ml.is_ready(cid)
        out.append({"id": cid, **CHECK_META[cid], "ready": ready,
                    "demo": ready and ml.is_dummy(cid)})
    return out


@app.get("/api/tip")
def tip():
    return DAILY_TIPS[dt.date.today().timetuple().tm_yday % len(DAILY_TIPS)]


@app.post("/api/predict/{check}")
def predict(check: str, file: UploadFile = File(...), user=Depends(current_user)):
    if check not in ml.CHECKS:
        raise HTTPException(404, "Unknown check.")
    if not ml.is_ready(check):
        raise HTTPException(503, "This check is coming soon (its model is not installed yet).")
    raw = file.file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "Photo is too large (max 10 MB).")
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        raise HTTPException(400, "This file is not a valid photo.")

    quality = ml.quality_check(img)
    try:
        res = ml.predict(check, img)
    except Exception as e:                                   # broken or mismatched model file
        print("[error] predict failed:", repr(e))
        raise HTTPException(500, "The model could not read this photo. Please try another one.")
    cam = res.pop("cam")
    base, blended = ml.overlay(img, cam)

    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO history(user_id,check_type,label,confidence,status,probs,quality,has_heatmap,created)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (user["id"], check, res["label"], res["confidence"], res["status"],
             json.dumps(res["probs"]), json.dumps(quality), int(blended is not None), time.time()),
        )
        hid = cur.lastrowid
        row = dict(c.execute("SELECT * FROM history WHERE id=?", (hid,)).fetchone())
    Image.fromarray(base).save(db.UPLOADS / f"{hid}_img.jpg", quality=85)
    if blended is not None:
        Image.fromarray(blended).save(db.UPLOADS / f"{hid}_heat.png")
    return payload(row)


# ------------------------------------------------------------------ history
@app.get("/api/history")
def history(check: str | None = None, limit: int = 100, user=Depends(current_user)):
    limit = max(1, min(limit, 500))
    sql = "SELECT * FROM history WHERE user_id=?"
    args = [user["id"]]
    if check:
        sql += " AND check_type=?"
        args.append(check)
    sql += " ORDER BY created DESC LIMIT ?"
    args.append(limit)
    with db.conn() as c:
        rows = [dict(r) for r in c.execute(sql, args)]
    return [{"id": r["id"], "check": r["check_type"], "label": r["label"], "display": display_label(r["label"]),
             "confidence": r["confidence"], "status": r["status"], "created": r["created"]} for r in rows]


@app.get("/api/history/{hid}")
def history_one(hid: int, user=Depends(current_user)):
    return payload(own_row(hid, user))


@app.get("/api/history/{hid}/image")
def history_image(hid: int, kind: str = "img", user=Depends(current_user)):
    own_row(hid, user)
    path = db.UPLOADS / (f"{hid}_heat.png" if kind == "heat" else f"{hid}_img.jpg")
    if not path.exists():
        raise HTTPException(404, "Image not found.")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/history/{hid}/report")
def history_report(hid: int, user=Depends(current_user)):
    row = own_row(hid, user)
    pdf = build_pdf(user["name"], row, json.loads(row["probs"]),
                    db.UPLOADS / f"{hid}_img.jpg", db.UPLOADS / f"{hid}_heat.png")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="health-check-{hid}.pdf"'})


@app.delete("/api/history/{hid}")
def history_delete(hid: int, user=Depends(current_user)):
    own_row(hid, user)
    with db.conn() as c:
        c.execute("DELETE FROM history WHERE id=?", (hid,))
    db.remove_files_for(hid)
    return {"ok": True}


@app.delete("/api/history")
def history_clear(user=Depends(current_user)):
    with db.conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM history WHERE user_id=?", (user["id"],))]
        c.execute("DELETE FROM history WHERE user_id=?", (user["id"],))
    for hid in ids:
        db.remove_files_for(hid)
    return {"deleted": len(ids)}


# ----------------------------------------------------------------- frontend
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONT / "index.html", headers={"Cache-Control": "no-cache"})
