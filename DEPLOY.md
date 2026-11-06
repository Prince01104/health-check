# Free deploy (Streamlit Community Cloud)

Koi bhi link kholkar app use kar sakega aur feedback de sakega. Login nahi hai (guest mode), photo server par save nahi hoti.

## 1. GitHub par daalo
1. github.com par new **public** repo banao (naam: `health-check`).
2. Is folder ki files upload karo (web par "Add file > Upload files" ya git).
   - **Mat daalo:** `data/`, `.venv/`, `kaggle.json`, tokens, dataset ki images.
   - **Daalo:** `backend/`, `streamlit_app/`, `models/` (apni asli `oral4_model.keras`, `oral4_classes.json`, `skin_model.keras`, `skin_classes.json` ke saath, 100 MB se chhoti), `.streamlit/`.
3. Dummy models replace kar do, warna app "Demo model" warning dikhayega.

## 2. Streamlit par deploy
1. share.streamlit.io par GitHub se login karo > **Create app**.
2. Repo = `health-check`, Branch = `main`, **Main file path = `streamlit_app/streamlit_app.py`**.
3. **Advanced settings > Python version = 3.12**.
4. Deploy dabao. Pehli baar 5-10 minute lagte hain (TensorFlow install hota hai). Phir `xxxx.streamlit.app` link milega, wahi sabko bhejo.

## 3. Feedback kaise dekhein
- App ke andar feedback `data/feedback.csv` mein jata hai, **par free hosting par ye file restart par mit jati hai.**
- Pakka tareeka: ek Google Form banao, uska link Streamlit ke **Settings > Secrets** mein daalo:
  ```
  FEEDBACK_FORM_URL = "https://forms.gle/xxxx"
  ADMIN_KEY = "koi-lamba-secret"
  ```
  Result page par "detailed feedback (form)" button aa jayega. Form ke jawab Google Sheet mein hamesha rahenge.
- Quick feedback dekhne ke liye: `https://<app>.streamlit.app/?admin=<ADMIN_KEY>`.

## Dhyan rakhne ki baatein
- App 12 ghante koi na aaye to so jata hai; pehle visitor ko "Wake up" dabana padta hai (30-60 sec).
- Free RAM kam hai (~2.7 GB). 2 se 4 chhote CNN models theek chalte hain.
- Kisi ki bhi health photo ya DermNet jaisi copyrighted images repo mein mat daalo.
- Jahan link share karo wahan likho: "Prototype hai, AI screening only, doctor ka vikalp nahi."
- Agar kabhi RAM ki dikkat aaye: `streamlit_app/requirements.txt` mein `tensorflow-cpu` already hai, models ko `.keras` ke bajay `tflite` mein badalna agla step hai.

## Local test
```
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/streamlit_app.py
```
