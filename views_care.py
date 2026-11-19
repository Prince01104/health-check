"""Check, progress, Aira chat, tips and news, acne tracker, sleep and insomnia screens."""
import hashlib
import io
import time
from urllib.parse import quote

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

import services as S
import ui


# =================================================================== CHECKS
def check() -> None:
    key = st.session_state.get("check_key", "skin")
    cfg = S.CHECKS[key]
    ui.back_button("home")
    st.markdown(f"# {cfg['title']}")
    ui.banner(key)
    st.caption(cfg["hint"])

    if not S.model_ready(key):
        ui.card(
            '<div style="font-weight:800;font-size:16px">Coming soon</div>'
            '<div class="hc-muted" style="margin-top:6px">This check is not ready yet because its model has not been '
            'trained and added. See models/README.txt to add one.</div>'
        )
        return
    with st.spinner("Loading the model (first time only)..."):
        S.load_models()
    if S.is_demo(key):
        st.warning("Demo model: the results are random and not meaningful.")

    with st.expander("Optional: a few questions for better guidance"):
        risk_form(f"check_{key}")

    source = st.radio("Photo source", ["Upload", "Camera"], horizontal=True, label_visibility="collapsed")
    if source == "Upload":
        photo = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"])
    else:
        photo = st.camera_input("Take a photo")
    if photo is None:
        return

    data = photo.getvalue()
    photo_id = hashlib.md5(data).hexdigest()
    try:
        preview = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        preview.thumbnail((900, 900))
    except (OSError, ValueError):
        st.error("This file is not a valid photo. Please try another one.")
        return
    done = st.session_state.results.get(key)
    if not (done and done["photo"] == photo_id):      # once there is a result, the result comes first (the photo is in its tabs)
        st.image(preview)

    ui.secure_note("Your photo is checked in memory and never saved.")
    if st.button("Analyze photo", type="primary", icon=":material/auto_awesome:", key=f"run_{key}"):
        try:
            with st.spinner("Aira is looking at your photo..."):
                res = S.analyse(key, io.BytesIO(data))
        except Exception as exc:                       # show a friendly message, keep the real error in the log
            print("[error] analyse failed:", repr(exc))
            st.error("Something went wrong with this photo. Please try another one.")
            return
        res["photo"] = photo_id
        S.record(res)
        st.session_state.results[key] = res
        st.rerun()

    res = st.session_state.results.get(key)
    if res and res["photo"] == photo_id:
        _show_result(key, res)


def _show_result(key: str, res: dict) -> None:
    status, label, prob = res["status"], res["label"], res["confidence"]
    doctor = S.CHECKS[key]["doctor"]
    info = S.info_for(key, label)

    for warning in res["quality"]["warnings"]:
        st.warning(S.QUALITY_TEXT.get(warning, warning))

    _result_card(res)
    _next_step(res)
    _change(res)

    if res["heat"] is not None:
        tab_photo, tab_heat = st.tabs(["Photo", "Heatmap"])
        with tab_photo:
            st.image(res["base"])
        with tab_heat:
            st.image(res["heat"])
            st.caption("Warm colours show where the AI looked. It is only a hint, not proof.")

    if status != "invalid" and S.is_red_flag(label):
        st.warning(f"This type of result needs a doctor. Please see a {doctor} soon.")

    if status == "ok":
        st.markdown("**About this result**")
        st.write(info["en"]["about"])
        st.markdown("**What you can do**")
        for tip in info["en"]["tips"]:
            st.markdown(f"- {tip}")
        advice = {"soon": f"Please book a visit with a {doctor} soon.",
                  "no": "Nothing worrying was seen, but regular check-ups are still a good idea."}
        st.info(advice.get(info["see_doctor"], "If it does not settle in 1 to 2 weeks or gets worse, please see a doctor."))
    elif status == "uncertain":
        st.info("If you are worried, please see a doctor.")

    with st.expander("Other possibilities"):
        for item in res["probs"][:4]:
            st.progress(min(max(item["p"], 0.0), 1.0), text=f"{S.pretty(item['label'])}  {item['p'] * 100:.0f}%")

    if status != "invalid":
        _chat(key, res)

    st.link_button(f"Find a {doctor} near me", "https://www.google.com/maps/search/" + quote(f"{S.DOCTOR_SEARCH[doctor]} near me"),
                   icon=":material/location_on:", use_container_width=True)
    _feedback(key, res)


def _result_card(res: dict) -> None:
    status, label, prob = res["status"], res["label"], res["confidence"]
    if status == "ok":
        ui.card(
            '<div class="hc-muted" style="font-weight:700">MOST LIKELY (SCREENING, NOT A DIAGNOSIS)</div>'
            f'<div style="font-size:24px;font-weight:800">{ui.esc(S.pretty(label))}</div>'
            f'<div class="hc-muted">{prob * 100:.0f}% confidence</div>'
        )
    elif status == "uncertain":
        why = ("The photo quality is too low to trust a result." if res.get("demoted")
               else "The model is not confident about this photo.")
        ui.card(
            '<div style="font-size:12px;font-weight:800;color:#8A3A10">RESULT</div>'
            '<div style="font-size:22px;font-weight:800">Not sure</div>'
            f'<div class="hc-muted" style="margin-top:4px">{why} Please retake it in good light, closer to the '
            f'problem area, or see a doctor.<br>Best guess: <b>{ui.esc(S.pretty(label))}</b> ({prob * 100:.0f}%)</div>',
            "border-color:#B4531A",
        )
    else:
        ui.card(
            '<div style="font-size:22px;font-weight:800">This photo does not look right</div>'
            '<div class="hc-muted" style="margin-top:4px">Please take a clear photo of the correct area and try again.</div>',
            "border-color:#B4531A",
        )


def _next_step(res: dict) -> None:
    nxt = res["next"]
    reasons = "".join(f"<li>{ui.esc(r)}</li>" for r in nxt["reasons"])
    ui.card(
        '<div class="hc-muted" style="font-weight:700">YOUR NEXT STEP</div>'
        f'<div style="font-size:20px;font-weight:800;color:{nxt["color"]}">{ui.esc(nxt["title"])}</div>'
        f'<div style="margin-top:4px">{ui.esc(nxt["text"])}</div>'
        + (f'<ul class="hc-muted" style="margin:8px 0 0 0;padding-left:18px">{reasons}</ul>' if reasons else ""),
        f"border-color:{nxt['color']};border-width:2px",
    )
    if res["risk"]["level"] != "unknown":
        st.caption(f"Risk factors you gave: {res['risk']['level']} (a simple count, not a medical score).")


def _change(res: dict) -> None:
    ch = res["change"]
    if not ch["has_prev"]:
        st.caption("This is your first check of this type in this record. Check again in about 2 weeks to see changes.")
        return
    color = "#B3261E" if ch["alert"] else "#0B6665"
    title = "Change noticed: worth a specialist's review" if ch["alert"] else "No big change since your last check"
    days = f" ({ch['days']:.0f} days ago)" if ch["days"] is not None and ch["days"] >= 1 else ""
    lines = "".join(f"<li>{ui.esc(x)}</li>" for x in ch["lines"])
    ui.card(
        f'<div class="hc-muted" style="font-weight:700">COMPARED WITH YOUR LAST CHECK{days}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{color}">{title}</div>'
        + (f'<ul class="hc-muted" style="margin:8px 0 0 0;padding-left:18px">{lines}</ul>' if lines else ""),
        f"border-color:{color}",
    )
    if res.get("prev_thumb") is not None:
        left, right = st.columns(2)
        left.image(res["prev_thumb"], caption="Before")
        right.image(res["thumb"], caption="Now")
    st.caption("Change alerts are an early prototype. The AI was not trained on photo pairs, and the limits are not "
               "clinically validated. A doctor decides what a change means.")


RISK_LABELS = {
    "age": "Age group", "tobacco": "Tobacco use", "alcohol": "Regular alcohol", "diabetes": "Diabetes",
    "family": "Skin or mouth cancer in the family", "sun": "Sun exposure",
    "duration": "How long have you had the problem?",
    "changing": "Is it growing, bleeding or changing colour or shape?",
}


def risk_form(prefix: str) -> None:
    """Optional self-reported risk factors. They stay in this visit only and never go to Gemini."""
    cur = S.risk_answers()
    with st.form(f"risk_form_{prefix}"):
        picked = {}
        for field, options in S.triage.RISK_FIELDS.items():
            idx = options.index(cur[field]) if cur.get(field) in options else 0
            picked[field] = st.selectbox(RISK_LABELS[field], options, index=idx, key=f"risk_{prefix}_{field}")
        saved = st.form_submit_button("Save answers")
    if saved:
        st.session_state.risk = picked
        st.success("Saved for this visit.")
    st.caption("Optional. Used only to make the next-step advice more careful. Not sent to Gemini and not saved on the server.")


# =================================================================== PROGRESS
def progress() -> None:
    ui.back_button("home")
    st.markdown("# My Progress")
    st.caption("See how your checks change over time. Photos are never saved. Only result numbers are kept, and only "
               "for this visit, unless you download your progress file below.")
    hist = st.session_state.history
    shown = False
    for key, cfg in S.CHECKS.items():
        rows = [e for e in hist if e["check"] == key]
        if not rows:
            continue
        shown = True
        st.markdown(f"### {cfg['title']}")
        latest = rows[-1]
        for e in rows:
            for line in e.get("alert_lines") or []:
                st.warning(f"{e['time']}: {line}")
        if len(rows) >= 2 and latest["status"] != "invalid":
            label = latest["label"]
            vals = [next((p["p"] for p in e["probs"] if p["label"] == label), 0.0) * 100 for e in rows]
            names = [f"{i + 1}. {e['time'][-5:]}" for i, e in enumerate(rows)]        # unique labels, even in the same minute
            df = pd.DataFrame({"check": names, f"{S.pretty(label)} (%)": vals}).set_index("check")
            st.line_chart(df, height=200)
            st.caption(f"How strongly the AI saw {S.pretty(label).lower()} in each photo.")
        else:
            st.caption("One check so far. Check again later to see a trend.")
        for e in reversed(rows):
            title = S.pretty(e["label"]) if e["status"] == "ok" else ("Not sure" if e["status"] == "uncertain" else "Photo not suitable")
            ui.card(f'<div class="hc-muted">{ui.esc(e["time"])}</div><div style="font-weight:800">{ui.esc(title)}</div>'
                    f'<div class="hc-muted">Next step: {ui.esc(e.get("next_step") or "")}</div>')
    if not shown:
        ui.card('<div style="font-weight:700">No checks yet</div><div class="hc-muted">Run a Skin or Oral check, or load '
                'a progress file from an earlier visit below.</div>')

    st.markdown("### Keep your record")
    if hist:
        st.download_button("Download summary for a doctor", S.summary_for_doctor(), file_name="health-check-summary.txt",
                           mime="text/plain", use_container_width=True, icon=":material/description:")
        st.download_button("Download my progress file", S.export_progress(), file_name="health-check-progress.json",
                           mime="application/json", use_container_width=True, icon=":material/download:")
        st.caption("The summary is plain text you can show a doctor. The progress file lets you continue next time. "
                   "Neither has your photos.")
    up = st.file_uploader("Load a progress file from an earlier visit", type=["json"], key="progress_upload")
    if up is not None and st.button("Load file", key="progress_load"):
        ok, msg = S.import_progress(up.getvalue())
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()


# ---- Aira chat (Gemini)
def _ask(key: str, question: str) -> None:
    """Send one question. Gemini only gets text (top predictions + chat), never the photo."""
    res = st.session_state.results[key]
    question = question.strip()[:500]
    if sum(1 for role, _ in res["chat"] if role == "user") >= S.MAX_QUESTIONS:
        res["chat"].append(("err", S.CHAT_ERRORS["limit"]))
        return
    with st.spinner("Aira is thinking..."):
        out = S.ask_aira(res, question)            # reads the chat BEFORE the new question is added
    res["chat"].append(("user", question))
    if out["ok"]:
        res["chat"].append(("aira", out["reply"]))
    else:
        res["chat"].append(("err", S.CHAT_ERRORS.get(out["error"], S.CHAT_ERRORS["unavailable"])))


def _chat(key: str, res: dict) -> None:
    st.markdown("### Ask Aira")
    st.caption("AI assistant, not a doctor. It only uses the result above. Your photo is not sent, only the result text "
               "and your messages go to Google Gemini.")
    for role, text in res["chat"]:
        if role == "err":
            st.warning(text)
        else:
            with st.chat_message("user" if role == "user" else "assistant"):
                st.write(text)

    if not S.gemini_available():
        st.caption("Aira's chat is off. Add GEMINI_API_KEY in the app secrets to turn it on.")
        return
    if not res["chat"]:
        if st.button("Explain this in simple words", key=f"explain_{key}"):
            _ask(key, "Explain this result in simple words and what I should do next.")
            st.rerun()
    with st.form(f"chat_form_{key}", clear_on_submit=True):
        question = st.text_input("Your question", placeholder="Ask anything about this result",
                                 label_visibility="collapsed", max_chars=500)
        sent = st.form_submit_button("Send")
    if sent and question.strip():
        _ask(key, question)
        st.rerun()


# ---- feedback
def _feedback(key: str, res: dict) -> None:
    st.markdown("### Was this helpful?")
    if res["feedback_done"]:
        st.success("Thank you! Your feedback was saved.")
    else:
        with st.form(f"fb_form_{key}", clear_on_submit=True):
            helpful = st.radio("Helpful", ["Yes", "No"], horizontal=True, label_visibility="collapsed")
            comment = st.text_input("Anything we should improve? (optional)", max_chars=300)
            if st.form_submit_button("Send feedback"):
                S.save_feedback(res, helpful.lower(), comment)
                res["feedback_done"] = True
                st.rerun()
        st.caption("Only your answer and comment are saved. The photo and your name are not saved.")
    url = S.feedback_form_url()
    if url:
        st.link_button("Give detailed feedback (form)", url, use_container_width=True)


# =================================================================== ACNE
def _level(score: int) -> str:
    if score <= 30:
        return "Very mild"
    if score <= 50:
        return "Mild"
    if score <= 70:
        return "Moderate"
    return "Severe"


def acne() -> None:
    ui.back_button("home")
    st.markdown("# Acne Tracker")
    log = st.session_state.acne_log
    scores = [e["score"] for e in log]
    real = [e["score"] for e in log if not e.get("sample")]

    # The trend uses only the user's own check-ins. The sample points are just there to show the chart.
    if len(real) >= 4:
        diff = sum(real[-2:]) / 2 - sum(real[:2]) / 2
    elif len(real) >= 2:
        diff = real[-1] - real[0]
    else:
        diff = 0

    if len(real) < 2:
        status, bg, ink, line, arrow = "Add more check-ins", "#E9F0EF", "#274547", "#0B6665", ""
        detail = ("The chart starts with sample points so you can see how it looks. Save your own check-ins below and "
                  "Aira will show your real trend." if not real else "Save at least two check-ins to see your trend.")
    elif diff <= -5:
        status, bg, ink, line, arrow = "Improving", "#DDF3E6", "#14603A", "#1E7A4C", "↓ "
        detail = f"Down {abs(round(diff))} points since you started. Your routine seems to be working, keep going."
    elif diff >= 5:
        status, bg, ink, line, arrow = "Getting worse", "#FBE6DE", "#8A3A10", "#B4531A", "↑ "
        detail = (f"Up {round(diff)} points since you started. If it keeps rising, becomes painful or leaves marks, "
                  "please see a dermatologist.")
    else:
        status, bg, ink, line, arrow = "About the same", "#E9F0EF", "#274547", "#0B6665", ""
        detail = "Your acne has stayed about the same. Keep the routine steady and check again next week."

    current = real[-1] if real else None
    score_html = (f'{current}<span class="hc-muted" style="font-size:15px;font-weight:600"> / 100 &#183; {_level(current)}</span>'
                  if current is not None else '<span class="hc-muted" style="font-size:20px;font-weight:700">No check-in yet</span>')
    ui.card(
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
        '<div><div class="hc-muted">Your latest acne score</div>'
        f'<div style="font-size:34px;font-weight:800;letter-spacing:-0.02em">{score_html}</div></div>'
        f'<span class="hc-pill" style="background:{bg};color:{ink}">{arrow}{status}</span></div>'
        f'<p style="margin:10px 0 0 0;font-size:14px;line-height:1.5">{detail}</p>'
    )
    df = pd.DataFrame({"Acne score (lower is better)": scores}, index=range(1, len(scores) + 1))
    st.line_chart(df, height=200, color=line)

    if any(e.get("sample") for e in log):
        st.caption("The first points are sample data so you can see how the tracker looks.")
        st.button("Clear sample data", key="clear_sample", on_click=_clear_sample)

    st.markdown("### Today's check-in")
    st.slider("How is your acne today? 0 is clear, 100 is severe", 0, 100, 40, key="acne_slider")
    st.button("Save check-in", type="primary", key="acne_save", on_click=_save_acne)
    st.caption("This is a self-rating, not a photo score. The Skin Check can tell you if a photo looks like acne.")

    ui.card('<b>Aira\'s tip:</b> take each photo in the same light, at the same angle, without filters, '
            'so the weekly comparison stays fair.')


def _clear_sample() -> None:
    st.session_state.acne_log = [e for e in st.session_state.acne_log if not e.get("sample")]


def _save_acne() -> None:
    st.session_state.acne_log.append({"score": int(st.session_state.acne_slider), "sample": False})


# =================================================================== SLEEP
def _start_sleep() -> None:
    st.session_state.sleep_on = True
    st.session_state.sleep_end = time.time() + int(st.session_state.sleep_minutes) * 60


def _stop_sleep() -> None:
    st.session_state.sleep_on = False


@st.fragment(run_every=1)
def _countdown() -> None:
    left = int(st.session_state.sleep_end - time.time())
    if left <= 0 or not st.session_state.sleep_on:
        st.session_state.sleep_on = False
        st.rerun()
    mins, secs = divmod(left, 60)
    st.markdown(f"**Stops in {mins:02d}:{secs:02d}**")


def sleep() -> None:
    ui.back_button("home")
    st.markdown("# Sleep Mode")
    ui.html(f"""
    <div class="hc-card" style="display:flex;align-items:center;gap:14px">
      <div class="aira-float" style="flex:none">{ui.aira(70, sleepy=True, suffix="s")}</div>
      <div class="hc-muted" style="font-size:15px">Dim the lights, relax your shoulders and let the sound slow your breathing.</div>
    </div>
    """)

    index = st.radio(
        "Sounds for sleep", range(len(S.SOUNDS)), format_func=lambda i: S.SOUNDS[i]["name"],
        captions=[s["note"] for s in S.SOUNDS], key="sleep_sound",
    )
    st.radio("Stop sound after", [15, 30, 45, 60], format_func=lambda m: f"{m} min",
             horizontal=True, key="sleep_minutes")

    if st.session_state.sleep_on:
        st.audio(S.sound_path(index), format="audio/wav", loop=True, autoplay=True)
        _countdown()
        st.button("Stop", key="sleep_stop", on_click=_stop_sleep)
    else:
        st.button("Start sleep sounds", type="primary", key="sleep_start", on_click=_start_sleep)

    st.markdown("---")
    st.button("Can't sleep? Take the insomnia check", icon=":material/psychology:", key="to_insomnia",
              on_click=ui.go, args=("insomnia",))


# =================================================================== INSOMNIA
QUESTIONS = [
    "Does it take you more than 30 minutes to fall asleep?",
    "Do you wake up at night and find it hard to fall back asleep?",
    "Do you use your phone in bed before sleeping?",
    "Do you feel tired in the day even after a full night in bed?",
    "Is this happening 3 or more nights every week?",
]
TIPS = [
    ("Breathe 4-7-8", "Breathe in for 4 counts, hold for 7, breathe out for 8. Repeat 4 times in bed."),
    ("Get up if awake for 20 minutes", "Sit in dim light and do something calm, then return when sleepy. "
     "Lying awake teaches the brain that bed means worry."),
    ("No screens for the last hour", "Keep the phone away from the bed. Use Sleep Mode sounds with the screen face down."),
    ("Wake up at the same time daily", "A fixed wake time, even on holidays, sets your body clock within a week or two."),
    ("Talk to a doctor soon", "Trouble on most nights can have causes that a doctor can find, such as stress or health conditions."),
]
GENERAL_TIPS = [
    ("Keep the room dark and cool", "A cool, quiet, dark room helps the body start sleep."),
    ("Stop caffeine after 2 pm", "Tea, coffee and energy drinks can keep you alert for 6 hours or more."),
]


def insomnia() -> None:
    ui.back_button("sleep")
    st.markdown("# Insomnia Check")
    st.caption("Think about the last 2 weeks. Choose Yes or No for each question.")

    answers = []
    for i, question in enumerate(QUESTIONS):
        answers.append(st.radio(question, ["Yes", "No"], index=None, horizontal=True, key=f"ins_{i}"))

    yes = sum(1 for a in answers if a == "Yes")
    answered = sum(1 for a in answers if a is not None)
    if answered < len(QUESTIONS):
        st.caption(f"{answered} of {len(QUESTIONS)} answered")
        return

    if yes <= 1:
        title, text, bg, ink = "Your sleep looks fine", "Keep your routine steady and use Sleep Mode when you want to relax.", "#D8F3E4", "#10432A"
    elif yes <= 3:
        title, text, bg, ink = "Mild sleep trouble", "A few small habit changes often help within 1 to 2 weeks. Try the ideas below.", "#FFE8B8", "#4A3200"
    else:
        title, text, bg, ink = "Possible insomnia", "Try the ideas below. If it continues for 3 weeks, please see a doctor.", "#FFD9CC", "#5A1E0C"
    ui.card(
        f'<div style="font-size:12px;font-weight:800;letter-spacing:.04em">YOUR RESULT &#183; {yes} OF 5 YES</div>'
        f'<div style="font-size:20px;font-weight:800;margin:4px 0">{title}</div>'
        f'<div style="font-size:14px;line-height:1.5">{text}</div>',
        f"background:{bg};border-color:{bg};color:{ink}",
    )

    ideas = [TIPS[i] for i, a in enumerate(answers) if a == "Yes"]
    for tip in GENERAL_TIPS:
        if len(ideas) < 3:
            ideas.append(tip)
    st.markdown("### Ideas that can help you")
    for n, (head, body) in enumerate(ideas[:3], start=1):
        ui.card(f'<b>{n}. {head}</b><div class="hc-muted" style="margin-top:2px">{body}</div>')
    st.caption("This is not a diagnosis. If trouble sleeping lasts 3 weeks or more, talk to a doctor.")
    st.button("Play sleep sounds", type="primary", key="ins_to_sleep", on_click=ui.go, args=("sleep",))


# =================================================================== TALK WITH AIRA
def aira() -> None:
    ui.back_button("home")
    st.markdown("# Talk with Aira")
    results = st.session_state.get("results", {})
    if not results:
        ui.card('<div style="font-weight:800;font-size:17px">Run a check first</div>'
                '<div class="hc-muted" style="margin-top:4px">Aira explains your result in simple words. '
                'Take a Skin or Oral check, then come back here or ask on the result screen.</div>')
        left, right = st.columns(2)
        left.button("Skin check", key="aira_go_skin", on_click=ui.go, args=("check",), kwargs={"check_key": "skin"})
        right.button("Oral check", key="aira_go_oral", on_click=ui.go, args=("check",), kwargs={"check_key": "oral"})
        st.caption("AI assistant, not a doctor. It cannot diagnose.")
        return
    key = max(results, key=lambda k: results[k]["ts"])
    res = results[key]
    title = S.pretty(res["label"]) if res["status"] == "ok" else "Not sure"
    ui.card(f'<div class="hc-muted" style="font-weight:700">YOUR LATEST RESULT &#183; {ui.esc(S.CHECKS[key]["title"].upper())}</div>'
            f'<div style="font-size:20px;font-weight:800">{ui.esc(title)}</div>'
            f'<div class="hc-muted">{ui.esc(res["next"]["title"])}</div>')
    _chat(key, res)


# =================================================================== HEALTH TIPS AND NEWS
def tips() -> None:
    ui.back_button("home")
    st.markdown("# Health tips")
    st.markdown("### Daily health news")
    items = S.health_news()
    if not items:
        st.caption("News is not available right now. Here are care ideas instead.")
    for it in items:
        ui.card(f'<a href="{ui.esc(it["link"])}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#1B2A4A;font-weight:800;font-size:15px;line-height:1.35;text-decoration:none">{ui.esc(it["title"])}</a>'
                f'<div class="hc-muted" style="margin-top:4px;font-size:12px">{ui.esc(it["source"])}'
                f'{" &#183; " + ui.esc(it["ago"]) if it["ago"] else ""}</div>')
    if items:
        st.caption("Headlines come from public news feeds and open the publisher's site. Aira does not write or check them. "
                   "They are general news, not advice for you.")
    st.markdown("### Care ideas")
    for tip in S.content.DAILY_TIPS[:8]:
        ui.card(f'<div style="font-size:14px;line-height:1.45">{ui.esc(tip["en"])}</div>')
