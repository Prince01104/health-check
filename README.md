# Health Check with Aira

A phone-style web app for early photo screening of the mouth and skin, built with Streamlit.
It is a screening aid. It is not a doctor and it never gives a diagnosis.

## What it does
- **Oral Check** and **Skin Check**: a CNN looks at a photo, shows the most likely result and a Grad-CAM heatmap of where it looked.
  Infection and Nail checks show "Coming soon" until their models are trained.
- **Your next step**: every result ends in one clear step: retake the photo, keep watching, or see a doctor soon.
  Blurry, dark, small or low-confidence photos are never shown as a confident result.
- **Risk factors (optional)**: a few self-reported answers (tobacco, diabetes, how long, changing lesion, and so on) make the advice more careful.
  This is a simple count, not a clinical score.
- **Change over time**: a new photo is compared with the last one of the same check. The app flags a changed result, a big shift in the
  AI's answer or photo "fingerprint", and a mouth ulcer that lasts 2 weeks or more, and says why. Alerts are meant for a specialist's review.
  The model was not trained on photo pairs and the thresholds are not clinically validated.
- **My Progress**: timeline, trend chart, a plain-text summary to show a doctor, and a progress file to continue next visit.
- **Ask Aira**: a Gemini chat about the result. Only text goes to Gemini, never the photo. Safety rules are enforced in code.
- Acne Tracker, Sleep Mode and an honest "Feeling lonely?" page with Tele-MANAS 14416. Peer calling is **not live** and is labelled as coming soon.

## Privacy
- Photos are checked in memory and never saved. A tiny thumbnail stays in memory for this visit only.
- Results and answers live in the browser session. Download the progress file to keep them; it has numbers only, no photos and no name.
- Profile > Delete all my data clears everything from the visit. Feedback saves only the answer and a comment.
- Gemini gets the top predictions and the chat text only.

## Run it
```
python -m venv venv
venv\Scripts\activate          (Windows)   or   source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Python 3.12 is needed for tensorflow-cpu 2.21.

## Turn on the chat
Get a free key at https://aistudio.google.com/apikey. Locally, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste the key.
On Streamlit Cloud, paste `GEMINI_API_KEY = "..."` in App settings > Secrets. Never commit the key.

## Deploy on Streamlit Community Cloud
New app > this repo > main file `app.py` > Advanced settings: Python 3.12 > Secrets. Files saved on the server (feedback.csv) are cleared when the app restarts.

## Tests
`python -m pytest -q tests` (48 tests, no internet and no API key needed; Gemini is faked).

## Honest limits
Skin model: about 79% test accuracy and it over-predicts tinea. Oral model: about 96% on its test set, partly helped by photo style.
Change alerts and risk factors are simple rules for a prototype. Real clinical use would need validated data, ethics approval and a doctor in the loop.
