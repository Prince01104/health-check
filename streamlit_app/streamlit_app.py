"""Health Check, Streamlit version (guest mode, photos are NOT stored).

Run locally from the project folder:   streamlit run streamlit_app/streamlit_app.py
Deploy free on Streamlit Community Cloud (see README): main file = streamlit_app/streamlit_app.py
It reuses the same models, Grad-CAM, quality check and tips as the FastAPI app.
"""
import csv
import datetime as dt
import hmac
import os
import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend import ml                                   # noqa: E402
from backend.content import DAILY_TIPS, describe         # noqa: E402

FEEDBACK_CSV = Path(os.environ.get("HC_DATA_DIR", ROOT / "data")) / "feedback.csv"
Image.MAX_IMAGE_PIXELS = 40_000_000

st.set_page_config(page_title="Health Check", page_icon="🩺", layout="centered")

# ------------------------------------------------------------------- text
EMOJI = {"oral": "🦷", "skin": "🙂", "infection": "🩹", "nail": "💅"}
DOCTOR_Q = {"dentist": "dentist", "dermatologist": "dermatologist", "doctor": "doctor"}
DOCTOR_OF = {"oral": "dentist", "skin": "dermatologist", "infection": "doctor", "nail": "dermatologist"}
LABEL_HI = {
    "calculus": "टार्टर (कैलकुलस)", "gingivitis": "मसूड़ों की सूजन", "hypodontia": "दांतों की कमी",
    "mouth_ulcer": "मुंह का छाला", "caries": "कैविटी (दांत की सड़न)", "discoloration": "दांतों का रंग बदलना",
    "acne": "मुंहासे", "rosacea": "रोज़ेसिया", "eczema": "एक्ज़ीमा", "tinea": "दाद (टिनिया)",
    "psoriasis": "सोरायसिस", "vitiligo": "सफेद दाग (विटिलिगो)",
}
TX = {
    "en": {
        "tagline": "Oral, skin, infection and nail screening in one app",
        "disc": "AI screening only. It does not replace a doctor's diagnosis.",
        "quickTitle": "Start a quick check", "quickText": "Pick a check below, add a clear photo and get an instant AI result.",
        "choose": "Choose a check", "soon": "Coming soon", "demo": "Demo model", "tipDay": "Tip of the day",
        "privacy": "Your photo is processed in memory and is not saved on the server.",
        "titles": {"oral": "Oral Check", "skin": "Skin Check", "infection": "Infection Check", "nail": "Nail Check"},
        "subs": {"oral": "Teeth and gums", "skin": "Face, acne and rashes", "infection": "Wounds and spots", "nail": "Colour and shape"},
        "back": "Back", "photoTips": "How to take a good photo",
        "upload": "Upload / take photo", "camera": "Use camera", "uploadHelp": "Choose a photo (on a phone you can pick the camera)",
        "analyse": "Analyse photo", "analysing": "Analysing...", "loadingModels": "Loading models (first time only)...",
        "demoWarn": "Demo model: the results are random and not meaningful.",
        "soonText": "This check is coming soon. Its model is not installed yet.",
        "photo": "Photo", "heat": "Heatmap", "heatNote": "Warm colours show where the AI looked. It is only a hint, not proof.",
        "possible": "Possible", "confidence": "confidence", "notSure": "Not sure", "bestGuess": "Best guess",
        "notSureText": "The model is not confident about this photo. Retake it in good light, closer to the problem area, and try again.",
        "invalidTitle": "This photo does not look right", "invalidText": "Please take a clear photo of the correct area. See the tips below.",
        "q_low_res": "The photo is small. Move closer or use a higher quality photo.",
        "q_blurry": "The photo looks blurry. Hold the phone steady.",
        "q_dark": "The photo is too dark. Use more light.", "q_bright": "The photo is too bright. Avoid flash and glare.",
        "about": "About this result", "doThis": "What you can do", "others": "Other possibilities",
        "d_soon": "Please book a visit with a {d} soon.", "d_if_persists": "If it does not settle in 1 to 2 weeks or gets worse, please see a doctor.",
        "d_no": "Nothing worrying was seen, but regular check-ups are still a good idea.", "d_unsure": "If you are worried, please see a doctor.",
        "findDoc": "Find a {d} near me", "again": "Check again", "noProblem": "No clear problem", "badPhoto": "Photo not suitable",
        "doctors": {"dentist": "dentist", "dermatologist": "skin doctor", "doctor": "doctor"},
        "fbTitle": "Was this result helpful?", "fbYes": "👍 Yes", "fbNo": "👎 No", "fbComment": "Anything we should improve? (optional)",
        "fbSend": "Send feedback", "fbThanks": "Thank you! Your feedback was saved.", "fbForm": "Give detailed feedback (form)",
        "fbNote": "Only your answer and comment are saved. The photo and your name are not saved.",
        "badFile": "This file is not a valid photo.", "err": "Something went wrong with this photo. Please try another one.",
        "tipsBy": {
            "oral": ["Open your mouth wide and face the camera straight.", "Use bright light. Avoid flash glare.", "Show the teeth, gums or sore area up close.", "Keep the phone steady."],
            "skin": ["Use daylight, with no filter or beauty mode.", "Hold the phone 15 to 30 cm away.", "Keep the problem area in the centre.", "Move hair or glasses away from the area."],
            "infection": ["Show the wound or spot clearly in bright light.", "Include a little normal skin around it.", "Do not use a filter.", "Keep the phone steady."],
            "nail": ["Place your hand flat in good light.", "Remove nail polish if you can.", "Take a close-up of one or two nails.", "Keep the nail in the centre."],
        },
    },
    "hi": {
        "tagline": "मुंह, त्वचा, संक्रमण और नाखून की जांच, एक ही ऐप में",
        "disc": "यह सिर्फ AI स्क्रीनिंग है। यह डॉक्टर की जांच का विकल्प नहीं है।",
        "quickTitle": "जल्दी जांच शुरू करें", "quickText": "नीचे से जांच चुनें, साफ फोटो डालें और तुरंत AI नतीजा पाएं।",
        "choose": "जांच चुनें", "soon": "जल्द आ रहा है", "demo": "डेमो मॉडल", "tipDay": "आज की सलाह",
        "privacy": "आपकी फोटो सिर्फ मेमोरी में जांची जाती है, सर्वर पर सेव नहीं होती।",
        "titles": {"oral": "मुंह की जांच", "skin": "त्वचा की जांच", "infection": "संक्रमण जांच", "nail": "नाखून की जांच"},
        "subs": {"oral": "दांत और मसूड़े", "skin": "चेहरा, मुंहासे और चकत्ते", "infection": "घाव और दाग", "nail": "रंग और आकार"},
        "back": "वापस", "photoTips": "अच्छी फोटो कैसे लें",
        "upload": "फोटो डालें / लें", "camera": "कैमरा इस्तेमाल करें", "uploadHelp": "फोटो चुनें (फोन पर कैमरा भी चुन सकते हैं)",
        "analyse": "फोटो जांचें", "analysing": "जांच हो रही है...", "loadingModels": "मॉडल लोड हो रहे हैं (सिर्फ पहली बार)...",
        "demoWarn": "डेमो मॉडल: नतीजे बेतरतीब हैं और किसी काम के नहीं।",
        "soonText": "यह जांच जल्द आएगी। इसका मॉडल अभी नहीं लगा है।",
        "photo": "फोटो", "heat": "हीटमैप", "heatNote": "गर्म रंग दिखाते हैं कि AI ने कहां देखा। यह सिर्फ एक संकेत है, सबूत नहीं।",
        "possible": "संभावित", "confidence": "भरोसा", "notSure": "पक्का नहीं", "bestGuess": "सबसे संभावित",
        "notSureText": "मॉडल को इस फोटो पर भरोसा नहीं है। अच्छी रोशनी में, समस्या वाली जगह के पास से दोबारा फोटो लें।",
        "invalidTitle": "यह फोटो सही नहीं लग रही", "invalidText": "कृपया सही जगह की साफ फोटो लें। नीचे दी गई सलाह देखें।",
        "q_low_res": "फोटो छोटी है। पास जाएं या बेहतर क्वालिटी की फोटो लें।", "q_blurry": "फोटो धुंधली लग रही है। फोन को स्थिर पकड़ें।",
        "q_dark": "फोटो बहुत अंधेरी है। ज़्यादा रोशनी में लें।", "q_bright": "फोटो बहुत तेज़ रोशनी वाली है। फ्लैश और चमक से बचें।",
        "about": "इस नतीजे के बारे में", "doThis": "आप क्या कर सकते हैं", "others": "दूसरी संभावनाएं",
        "d_soon": "कृपया जल्द {d} से मिलें।", "d_if_persists": "अगर 1-2 हफ्ते में ठीक न हो या बढ़े, तो डॉक्टर को दिखाएं।",
        "d_no": "कुछ चिंताजनक नहीं दिखा, फिर भी नियमित जांच अच्छी रहती है।", "d_unsure": "अगर चिंता हो तो डॉक्टर को दिखाएं।",
        "findDoc": "पास के {d} खोजें", "again": "दोबारा जांचें", "noProblem": "कोई साफ समस्या नहीं", "badPhoto": "फोटो सही नहीं",
        "doctors": {"dentist": "डेंटिस्ट", "dermatologist": "त्वचा रोग विशेषज्ञ", "doctor": "डॉक्टर"},
        "fbTitle": "क्या यह नतीजा काम का था?", "fbYes": "👍 हां", "fbNo": "👎 नहीं", "fbComment": "हम क्या बेहतर करें? (ज़रूरी नहीं)",
        "fbSend": "फीडबैक भेजें", "fbThanks": "धन्यवाद! आपका फीडबैक सेव हो गया।", "fbForm": "विस्तार से फीडबैक दें (फॉर्म)",
        "fbNote": "सिर्फ आपका जवाब और कमेंट सेव होता है। फोटो और आपका नाम सेव नहीं होते।",
        "badFile": "यह फाइल सही फोटो नहीं है।", "err": "इस फोटो में कुछ गड़बड़ हुई। कृपया दूसरी फोटो आज़माएं।",
        "tipsBy": {
            "oral": ["मुंह पूरा खोलें और कैमरे की तरफ सीधे देखें।", "तेज़ रोशनी लें। फ्लैश की चमक से बचें।", "दांत, मसूड़े या घाव की पास से फोटो लें।", "फोन को स्थिर रखें।"],
            "skin": ["दिन की रोशनी में लें, फिल्टर या ब्यूटी मोड न लगाएं।", "फोन को 15 से 30 सेमी दूर रखें।", "समस्या वाली जगह को बीच में रखें।", "बाल या चश्मा उस जगह से हटा लें।"],
            "infection": ["घाव या दाग को तेज़ रोशनी में साफ दिखाएं।", "आसपास की थोड़ी सामान्य त्वचा भी लें।", "फिल्टर का उपयोग न करें।", "फोन को स्थिर रखें।"],
            "nail": ["हाथ को अच्छी रोशनी में सीधा रखें।", "हो सके तो नेल पॉलिश हटा लें।", "एक या दो नाखूनों की पास से फोटो लें।", "नाखून को बीच में रखें।"],
        },
    },
}

CSS = """
<style>
.block-container {max-width: 480px; padding-top: 1.4rem; padding-bottom: 3rem;}
.hc-banner {background:#0f6b66; color:#fff; border-radius:18px; padding:18px; margin:6px 0 4px;}
.hc-banner b {font-size:17px;} .hc-banner p {margin:4px 0 0; color:rgba(255,255,255,.88); font-size:14px;}
.hc-res {border-radius:16px; padding:16px; margin:10px 0;}
.hc-ok {background:#e4f4ee; color:#123b38;} .hc-warn {background:#fff3dc; color:#8a5300;} .hc-bad {background:#fde8e6; color:#a3271c;}
.hc-res h2 {margin:2px 0 6px; font-size:22px;} .hc-small {font-size:13px; opacity:.85;}
.hc-tip {background:#fff; border:1px solid #d9e6e4; border-radius:16px; padding:12px 14px; font-size:14px;}
.stButton > button, .stLinkButton > a {border-radius:14px; min-height:48px; font-weight:700;}
div[data-testid="stImage"] img {border-radius:14px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------- helpers
def _secret(name):
    v = os.environ.get(name)
    if v:
        return v
    try:
        return st.secrets.get(name)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_models():
    ml.warm_up()
    return True


def label_name(label: str, lang: str) -> str:
    low = label.lower()
    if low.startswith("not_"):
        return TX[lang]["badPhoto"]
    if "normal" in low:
        return TX[lang]["noProblem"]
    return LABEL_HI.get(low, ml.pretty(label)) if lang == "hi" else ml.pretty(label)


def save_feedback(r: dict, helpful: str, comment: str):
    FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    new = not FEEDBACK_CSV.exists()
    with open(FEEDBACK_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "check", "label", "confidence", "status", "helpful", "comment"])
        w.writerow([dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), r["check"], r["label"],
                    round(r["confidence"], 3), r["status"], helpful, comment.strip()[:500].replace("\n", " ")])


def analyse(check: str, file) -> dict:
    img = Image.open(file)
    img.load()
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    quality = ml.quality_check(img)
    res = ml.predict(check, img)
    cam = res.pop("cam")
    base, blended = ml.overlay(img, cam)
    res.update({"check": check, "quality": quality, "base": base, "heat": blended, "demo": ml.is_dummy(check)})
    return res


# ------------------------------------------------------------------ state
ss = st.session_state
ss.setdefault("view", "home")
ss.setdefault("check", None)
ss.setdefault("result", None)
ss.setdefault("fb_done", False)

top = st.columns([3, 2])
with top[1]:
    pick = st.radio("Language", ["English", "हिन्दी"], horizontal=True, label_visibility="collapsed", key="lang_pick")
lang = "hi" if pick == "हिन्दी" else "en"
t = TX[lang]

with top[0]:
    st.markdown("## Health Check")

with st.spinner(t["loadingModels"]):
    load_models()


def go(view, check=None):
    ss.view, ss.check = view, check
    if view != "result":
        ss.result, ss.fb_done = None, False


# ------------------------------------------------------------------- views
def view_home():
    st.caption(t["tagline"])
    st.markdown(f'<div class="hc-banner"><b>{t["quickTitle"]}</b><p>{t["quickText"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f"#### {t['choose']}")
    cols = st.columns(2)
    for i, c in enumerate(ml.CHECKS):
        ready = ml.is_ready(c)
        with cols[i % 2]:
            if st.button(f"{EMOJI[c]}  {t['titles'][c]}", key=f"pick_{c}", use_container_width=True, disabled=not ready):
                go("check", c)
                st.rerun()
            note = t["subs"][c]
            if not ready:
                note = f"🔒 {t['soon']}"
            elif ml.is_dummy(c):
                note = f"⚠️ {t['demo']}"
            st.caption(note)
    tip = DAILY_TIPS[dt.date.today().timetuple().tm_yday % len(DAILY_TIPS)]
    st.markdown(f'<div class="hc-tip">💡 <b>{t["tipDay"]}</b><br>{tip[lang]}</div>', unsafe_allow_html=True)


def view_check():
    c = ss.check
    if st.button(f"← {t['back']}", key="back_home"):
        go("home")
        st.rerun()
    st.markdown(f"### {EMOJI[c]} {t['titles'][c]}")
    if ml.is_dummy(c):
        st.warning(t["demoWarn"])
    with st.expander(t["photoTips"], expanded=True):
        for tip in t["tipsBy"][c]:
            st.markdown(f"- {tip}")

    tab_up, tab_cam = st.tabs([t["upload"], t["camera"]])
    with tab_up:
        up = st.file_uploader(t["uploadHelp"], type=["jpg", "jpeg", "png", "webp"], key=f"up_{c}")
    with tab_cam:
        cam = st.camera_input(t["camera"], key=f"cam_{c}", label_visibility="collapsed")
    photo = up or cam
    if photo is not None:
        st.image(photo, use_container_width=True)
    if st.button(t["analyse"], type="primary", use_container_width=True, disabled=photo is None, key="go"):
        try:
            with st.spinner(t["analysing"]):
                ss.result = analyse(c, photo)
            ss.fb_done = False
            ss.view = "result"
            st.rerun()
        except (OSError, ValueError):
            st.error(t["badFile"])
        except Exception as e:                      # model problem: show a friendly message, log the real one
            print("[error] analyse failed:", repr(e))
            st.error(t["err"])


def view_result():
    r = ss.result
    if r is None:
        go("home")
        st.rerun()
    c, status = r["check"], r["status"]
    info = describe(c, r["label"])
    doc_key = DOCTOR_OF[c]
    doc = t["doctors"][doc_key]
    conf = r["confidence"]
    name = label_name(r["label"], lang)

    if st.button(f"← {t['back']}", key="back_check"):
        go("check", c)
        st.rerun()
    st.markdown(f"### {EMOJI[c]} {t['titles'][c]}")
    if r["demo"]:
        st.warning(t["demoWarn"])

    if r["heat"] is not None:
        tab_p, tab_h = st.tabs([t["photo"], t["heat"]])
        with tab_p:
            st.image(r["base"], use_container_width=True)
        with tab_h:
            st.image(r["heat"], use_container_width=True)
            st.caption(t["heatNote"])
    else:
        st.image(r["base"], use_container_width=True)

    if status == "ok":
        st.markdown(f'<div class="hc-res hc-ok"><span class="hc-small">{t["possible"]}</span><h2>{name}</h2>'
                    f'<span class="hc-small">{conf:.0%} {t["confidence"]}</span></div>', unsafe_allow_html=True)
        st.progress(min(max(conf, 0.0), 1.0))
    elif status == "uncertain":
        st.markdown(f'<div class="hc-res hc-warn"><h2>{t["notSure"]}</h2>{t["notSureText"]}'
                    f'<p class="hc-small">{t["bestGuess"]}: <b>{name}</b> ({conf:.0%})</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="hc-res hc-bad"><h2>{t["invalidTitle"]}</h2>{t["invalidText"]}</div>', unsafe_allow_html=True)

    for w in r["quality"]["warnings"]:
        st.warning(t.get("q_" + w, w))

    if status == "ok":
        body = info[lang]
        st.markdown(f"**{t['about']}**")
        st.write(body["about"])
        st.markdown(f"**{t['doThis']}**")
        for tip in body["tips"]:
            st.markdown(f"- {tip}")
        sd = info["see_doctor"]
        st.info(t["d_soon"].format(d=doc) if sd == "soon" else t["d_no"] if sd == "no" else t["d_if_persists"])
    else:
        st.markdown(f"**{t['photoTips']}**")
        for tip in t["tipsBy"][c]:
            st.markdown(f"- {tip}")
        if status == "uncertain":
            st.info(t["d_unsure"])

    with st.expander(t["others"]):
        for p in r["probs"][:4]:
            st.progress(min(max(p["p"], 0.0), 1.0), text=f'{label_name(p["label"], lang)}  {p["p"]:.0%}')

    st.link_button(f"📍 {t['findDoc'].format(d=doc)}", "https://www.google.com/maps/search/" + quote(f"{DOCTOR_Q[doc_key]} near me"),
                   use_container_width=True)

    # ------------- feedback
    st.divider()
    st.markdown(f"**{t['fbTitle']}**")
    if ss.fb_done:
        st.success(t["fbThanks"])
    else:
        with st.form("fb_form", clear_on_submit=True):
            helpful = st.radio("helpful", [t["fbYes"], t["fbNo"]], horizontal=True, label_visibility="collapsed")
            comment = st.text_area(t["fbComment"], max_chars=500)
            if st.form_submit_button(t["fbSend"], use_container_width=True):
                save_feedback(r, "yes" if helpful == t["fbYes"] else "no", comment)
                ss.fb_done = True
                st.rerun()
        st.caption(t["fbNote"])
    form_url = _secret("FEEDBACK_FORM_URL")
    if form_url:
        st.link_button(t["fbForm"], form_url, use_container_width=True)

    if st.button(t["again"], type="primary", use_container_width=True, key="again"):
        go("check", c)
        st.rerun()


{"home": view_home, "check": view_check, "result": view_result}.get(ss.view, view_home)()

st.divider()
st.caption(t["disc"])
st.caption("🔒 " + t["privacy"])

# optional private page for the owner: open the app with ?admin=<ADMIN_KEY>
_key = _secret("ADMIN_KEY")
if _key and hmac.compare_digest(str(st.query_params.get("admin", "")), str(_key)):
    with st.expander("Admin: feedback"):
        if FEEDBACK_CSV.exists():
            import pandas as pd
            df = pd.read_csv(FEEDBACK_CSV)
            st.dataframe(df, use_container_width=True)
            st.download_button("Download feedback.csv", FEEDBACK_CSV.read_bytes(), "feedback.csv", "text/csv")
        else:
            st.write("No feedback yet.")
