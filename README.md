# Health Check (oral, skin, infection, nail screening)

Mobile-style web app: login, 4 checks, result with heatmap (Grad-CAM), history, PDF report, English/Hindi.
Backend: FastAPI + SQLite + TensorFlow. Frontend: plain HTML/CSS/JS (no build step).

> **AI screening only. It does not replace a doctor's diagnosis.** This is a learning project.

## Run karna (Windows)

1. Python 3.10+ chahiye. Is folder mein terminal kholo:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Server chalao:
   ```
   python -m uvicorn backend.main:app --port 8000
   ```
   (ya `run.bat` par double click)
3. Browser mein kholo: http://127.0.0.1:8000

**Phone par chalane ke liye** (phone aur computer same Wi-Fi par): `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`,
phir phone ke browser mein `http://<computer-ka-IP>:8000` kholo (IP ke liye `ipconfig`). "Take photo" button seedha camera kholta hai.

## Apne models lagana

Models `models/` folder mein rakho. Kaunsa check kaunsi file padhta hai, wo `models/registry.json` mein likha hai:

| Check | Model file | Classes file |
|---|---|---|
| Oral | `oral4_model.keras` | `oral4_classes.json` |
| Skin | `skin_model.keras` | `skin_classes.json` |
| Infection | `infection_model.keras` | `infection_classes.json` |
| Nail | `nail_model.keras` | `nail_classes.json` |

- Aapke Kaggle se download kiye `oral4_model.keras` aur `oral4_classes.json` seedha is folder mein daal do (purani dummy file replace ho jayegi).
- 3-class skin model (`skin3_model.keras`, `skin3_classes.json`) ko rename karke `skin_model.keras` / `skin_classes.json` kar do
  (ya `registry.json` mein naam badal do).
- Jis check ki model file nahi hai, uspar app "Coming soon" dikhata hai.
- **`classes.json` ka order wahi hona chahiye jo training ke `class_indices` mein tha.**
- Image size model se apne aap aata hai. Model ko `/255` wali tarah train kiya hona chahiye (jaise `rescale=1/255`).
- Dummy (random) models `python tools/make_dummy_models.py` se bante hain. Unpar app "Demo model" ki warning dikhata hai,
  jo asli model lagate hi apne aap hat jati hai.

### Thresholds (`registry.json`)
- `threshold`: isse kam confidence par result "Not sure" dikhta hai (abhi 0.70).
- `class_thresholds`: kisi class ke liye alag. Oral mein `mouth_ulcer` ke liye 0.90 hai, kyunki test mein ye model ki
  "default" class nikli (adhoori photos ko bhi ulcer bol deti thi).
- Class ka naam `not_...` se shuru ho (jaise `not_oral`) to result "Photo not suitable" dikhta hai.
- Class ke naam mein `normal` ho to result "No clear problem" dikhta hai.

## Features

Done: login/signup, 4 checks, confidence + "Not sure" message, photo quality warning (blur/dark/small),
Grad-CAM heatmap, history + delete, PDF report, nearby doctor link (Google Maps), daily tip, day streak,
Hindi/English, in-app daily reminder, account and data delete.

Abhi nahi: forgot-password (email service chahiye), push notifications jab app band ho, photo se height, chatbot.

## Privacy
- Photos aur results sirf `data/` folder mein rehte hain (isko GitHub par mat daalna, `.gitignore` mein pehle se hai).
- Profile > "Delete my account and data" sab kuch mita deta hai.
- Passwords PBKDF2 se hash hote hain. Login 30 din tak chalta hai.
- Ye app abhi sirf apne computer/Wi-Fi ke liye hai. Internet par daalne se pehle HTTPS aur secrets ka dhyan rakhna padega.

## Free online deploy
Streamlit version (guest mode, feedback form): `streamlit_app/` aur [DEPLOY.md](DEPLOY.md) dekho.

## Tests
```
pip install -r requirements-dev.txt
python -m pytest -q
```

## GitHub par daalne se pehle
- `data/`, `.venv/`, `kaggle.json` mat daalo. Dataset ki images mat daalo (DermNet jaisi images par copyright hai), sirf link do.
- Model file 100 MB se chhoti ho tabhi daalo.
- README mein model ki limitations likho (dataset bias, chhoti classes, shortcut tests).

## Folder
```
backend/   main.py (API), ml.py (model + Grad-CAM), db.py, content.py (tips EN/HI), report.py (PDF)
frontend/  index.html, style.css, app.js
models/    registry.json + model files
streamlit_app/  streamlit_app.py (free deploy version) + requirements.txt
tools/     make_dummy_models.py
tests/     test_api.py
data/      app.db + photos (apne aap banta hai)
```
