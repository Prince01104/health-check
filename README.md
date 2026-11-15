# Health Check

small demo : https://health-check-prince.streamlit.app/#health-check

A small web app that looks at a photo and gives a rough first opinion on four things: mouth and teeth, skin, infections and nails. I built it as a learning project to practise training image classifiers and then putting them inside a real app.

**This is not a medical tool. It cannot diagnose anything and it is not a replacement for a doctor.** Please do not use it to make health decisions.

## What it does

- Four checks: Oral, Skin, Infection and Nail
- You upload or take a photo and get a possible result with a confidence score
- If the model is not confident, it says "Not sure" instead of guessing
- A Grad-CAM heatmap shows which part of the photo the model looked at
- Warns you when the photo is blurry, too dark, too bright or too small
- A "find a doctor near me" button that opens Google Maps
- A daily health tip, English and Hindi
- Feedback box after every result
- A chat box under every result where you can ask follow-up questions (powered by Gemini, see below)

The full version (FastAPI) also has login, history, PDF reports, a day streak and reminders. The Streamlit version is a lighter guest-mode copy made for free online hosting. It does not save photos.

## Current state of the models

Each check has its own small CNN built with TensorFlow/Keras and trained on Kaggle.

| Check | Classes | Test accuracy | Status |
|---|---|---|---|
| Oral | calculus, gingivitis, hypodontia, mouth ulcer | about 96% | working |
| Skin | acne, eczema, tinea, normal | about 79% | working |
| Infection | - | - | not trained yet |
| Nail | - | - | not trained yet |

The accuracy numbers look better than the models really are. Things I found while testing:

- The oral model has no "normal" or "not a mouth" class, so it will still pick one of the four diseases for any photo. Mouth ulcer ended up as its default answer, so it needs 90% confidence before I show it.
- Part of the oral accuracy comes from the model recognising the type of photo in each dataset, not the disease itself.
- The skin model over-predicts tinea. Its precision for that class is only about 47%.
- The "normal" skin class is easy because the images are things like hands, plain skin and even a dog.
- Many skin images come from DermNet and carry watermarks, so I added random watermark augmentation during training to stop the model from using that as a shortcut.
- Photos taken outside the datasets are the real test, and the results there are weaker than the numbers above.

Next things I want to try: a proper normal / not-oral class for the mouth model, transfer learning (MobileNetV2) for skin, and training the infection and nail models.

## Datasets

The training images are not in this repo. Some of them (DermNet especially) are copyrighted, and photos of people's health problems should not be re-shared. The oral and skin images came from public Kaggle datasets and a Mendeley dataset. If you want to retrain, get the data from the original sources.

## Project layout

```
backend/        FastAPI app, model loading, Grad-CAM, database, PDF report, tips (EN/HI), chat.py (Gemini chat)
frontend/       plain HTML, CSS and JavaScript for the FastAPI version
streamlit_app/  the Streamlit version (guest mode) and its requirements
models/         registry.json and the trained .keras model files
tools/          script that makes random dummy models for testing
tests/          API and chat tests
Dockerfile      for Google Cloud Run (FastAPI version)
```

## Run it on your computer

You need Python 3.10 or newer.

**Streamlit version**

```
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/streamlit_app.py
```

**Full version (login, history, PDF)**

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --port 8000
```

Then open http://127.0.0.1:8000. On Linux or Mac use `source .venv/bin/activate` instead of the activate line above.

## Using your own models

Put the model and its class list in `models/`. `models/registry.json` says which file each check reads. The order of names in the classes file must match the order used during training. The model should expect images scaled by 1/255. If a check has no model file, the app shows "Coming soon" for it.

In `registry.json` you can also set the confidence threshold for each check, and a different threshold for a single class. A class whose name starts with `not_` is shown as "photo not suitable", and a class with `normal` in its name is shown as "no clear problem".

If no real model is found you can run `python tools/make_dummy_models.py` to create random ones for testing. The app shows a warning on those because their answers mean nothing.

## Hosting it for free

The Streamlit version can run on Streamlit Community Cloud. Steps are in [DEPLOY.md](DEPLOY.md). The free app goes to sleep after a while without visitors and does not keep files, so feedback is better collected with a Google Form.

## Chatbot (Gemini)

Under every result there is a chat box. The user can ask what the result may mean, get basic care tips, or ask when to see a doctor, and Gemini answers in simple English, Hindi or Hinglish. The chat remembers the earlier messages and the model result.

**How it works**

1. Our own CNN predicts as before. The top 3 predictions with confidence, for example "Psoriasis 78%, Eczema 15%, Tinea 5%", are put into the system prompt.
2. The user's question and the earlier messages go to Gemini (`gemini-3.5-flash` by default, change it with the `GEMINI_MODEL` variable).
3. The answer is shown in the chat. If Gemini fails or is slow, the user sees a friendly message and the result above stays as it is.

**What is sent to Gemini:** text only. That is the top predictions and the messages the user types. The photo, the user's name, email and account data are never sent. Users are told this under the chat box. Do not type personal details in the chat.

**Safety rules** (in `backend/chat.py`)

- It is a screening assistant, never a doctor, and never gives a final diagnosis.
- It uses only the model result. Below 60% confidence (or when the app shows "Not sure") it says "not sure" and advises seeing a doctor.
- No prescription medicines or doses, only general care tips.
- A cancer-type label, or the user mentioning fever, fast-spreading redness, pus or severe pain, always gives "see a dermatologist soon" (a dentist for the oral check).
- Short answers in the user's language, always ending with a one-line "AI screening, not a diagnosis" reminder.

These rules are in the prompt and also checked again in code after the answer comes back, so the doctor advice, the "not sure" line and the reminder are added if the model forgets them. Limits: 500 characters per message, 20 questions per 10 minutes per user in the full app, 15 questions per result in the Streamlit demo.

**Get a free API key**

1. Open [Google AI Studio](https://aistudio.google.com/apikey) and sign in with a Google account.
2. Click **Create API key** and copy it.
3. Keep it secret. Never put it in the code, in a screenshot or on GitHub. The key is read from `GEMINI_API_KEY` only. The free tier has usage limits, so a busy public demo can show the "assistant is busy" message.

**Run locally**

Windows PowerShell:
```
$env:GEMINI_API_KEY="paste-your-key-here"
python -m uvicorn backend.main:app --port 8000
```
Windows cmd: `set GEMINI_API_KEY=paste-your-key-here`. Linux or Mac: `export GEMINI_API_KEY=paste-your-key-here`.

For the Streamlit version, create the file `.streamlit/secrets.toml` (it is in `.gitignore`):
```
GEMINI_API_KEY = "paste-your-key-here"
```
and run `streamlit run streamlit_app/streamlit_app.py`. On Streamlit Community Cloud, paste the same line in **Settings > Secrets**.

Without a key the app still works. The chat just says it is not set up.

## Deploy on Google Cloud Run

The `Dockerfile` runs the FastAPI version. You need a Google Cloud project with billing enabled and the `gcloud` tool.

```
gcloud services enable run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com
printf "paste-your-key-here" | gcloud secrets create gemini-api-key --data-file=-
gcloud run deploy health-check --source . --region asia-south1 --allow-unauthenticated \
  --memory 2Gi --cpu 2 --max-instances 1 --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

Notes:
- The service account that runs the service needs the *Secret Manager Secret Accessor* role on that secret.
- `--max-instances 1` is on purpose. Accounts and history are in SQLite inside the container, so they are lost when the container restarts. For a real launch, move them to Cloud SQL or Firestore.
- Use HTTPS (Cloud Run gives it) before sharing the link, and keep the disclaimer on.
- The first request after a quiet time is slow because TensorFlow loads the models.

## Privacy

- The Streamlit version keeps photos only in memory while the result is made. Nothing is saved.
- The full version stores photos and results in a local `data/` folder, which is in `.gitignore`. A user can delete their account and everything with it. Passwords are hashed with PBKDF2.
- The chat sends only text to Google Gemini (see the Chatbot section). Never upload `data/`, API keys, tokens, `.env`, `secrets.toml` or `kaggle.json` to GitHub.

## Tests

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## Not done yet

Forgot-password by email, push notifications while the app is closed, and estimating height from a photo.
