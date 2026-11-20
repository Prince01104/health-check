"""Check, progress, Aira chat, tips and news, acne tracker, sleep and insomnia screens."""
import base64
import datetime as dt
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
SUBTITLE = {"skin": "Acne, tinea, eczema or no clear problem", "oral": "Hypodontia, gingivitis, ulcer or calculus"}
ADD_ICON = ('<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#1B2A4A" stroke-width="1.8" stroke-linecap="round" '
            'stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5-5-8 8"/></svg>')


def _set_src(key: str, mode: str) -> None:
    st.session_state[f"srcmode_{key}"] = mode


def _source_tiles(key: str):
    """Two pastel tiles (Upload / Take photo) and the matching widget. Returns the chosen photo or None."""
    mode = st.session_state.get(f"srcmode_{key}", "up")
    left, right = st.columns(2)
    for col, m, label, icon in ((left, "up", "Upload photo", ":material/upload:"), (right, "cam", "Take photo", ":material/photo_camera:")):
        with col, st.container(key=f"src_{key}_{m}"):
            st.button(label, icon=icon, key=f"btn_{m}_{key}", on_click=_set_src, args=(key, m))
    st.markdown(f"<style>.st-key-src_{key}_{mode} button {{ box-shadow: 0 0 0 2.5px #0B6665 !important; }}</style>", unsafe_allow_html=True)
    if mode == "up":
        with st.container(key=f"drop_{key}"):
            return st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"], key=f"up_{key}", label_visibility="collapsed")
    return st.camera_input("Take a photo", key=f"cam_{key}", label_visibility="collapsed")


def _quick_questions(key: str) -> None:
    q = st.session_state.setdefault("quick", {}).setdefault(key, {})
    t = S.triage
    with st.container(key="quick"):
        ui.html('<div class="hc-q">How long has it been there?</div>')
        q["duration"] = st.pills("How long", t.DURATION_CHIPS, selection_mode="single", key=f"q_dur_{key}", label_visibility="collapsed")
        ui.html('<div class="hc-q">Any of these signs?</div>')
        q["signs"] = st.pills("Signs", t.SIGN_CHIPS[key], selection_mode="multi", key=f"q_sign_{key}", label_visibility="collapsed") or []
        ui.html('<div class="hc-q">Health background</div>')
        q["background"] = st.pills("Background", t.BACKGROUND_CHIPS[key], selection_mode="multi", key=f"q_bg_{key}", label_visibility="collapsed") or []


def check() -> None:
    key = st.session_state.get("check_key", "skin")
    cfg = S.CHECKS[key]
    ui.header(cfg["title"], SUBTITLE.get(key, cfg["blurb"]))

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

    ui.html('<div class="hc-h">1. Add a clear photo</div>')
    photo = _source_tiles(key)
    data = photo.getvalue() if photo is not None else None
    photo_id = hashlib.md5(data).hexdigest() if data else None
    preview = None
    if data:
        try:
            preview = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
            preview.thumbnail((900, 900))
        except (OSError, ValueError):
            st.error("This file is not a valid photo. Please try another one.")
            data = photo_id = None
    if preview is None:
        ui.html(f'<div class="hc-hint">{ui.esc(cfg["hint"])}</div>')
    else:
        with st.container(key=f"prev_{key}"):
            st.image(preview)
        try:
            warns = S.quality_of(io.BytesIO(data))["warnings"]
        except Exception:                                    # the pill is a bonus; never block the check
            warns = None
        if warns is not None:
            if warns:
                ui.html(f'<div class="hc-ok warn">{ui.esc(S.QUALITY_TEXT.get(warns[0], warns[0]))}</div>')
            else:
                ui.html('<div class="hc-ok"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#14603A" stroke-width="2.4" '
                        'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/></svg>'
                        'Photo is sharp and well lit</div>')

    ui.html('<div class="hc-h">2. Quick questions <small>optional</small></div>')
    _quick_questions(key)
    keep = st.checkbox("Keep this check in my history so I can compare later", key=f"keep_{key}")

    if st.button("Check now", type="primary", icon=":material/auto_awesome:", key=f"run_{key}"):
        if data is None:
            st.warning("Please add a photo first.")
        else:
            try:
                with st.spinner("Aira is looking at your photo..."):
                    res = S.analyse(key, io.BytesIO(data))
            except Exception as exc:                       # show a friendly message, keep the real error in the log
                print("[error] analyse failed:", repr(exc))
                st.error("Something went wrong with this photo. Please try another one.")
                return
            res["photo"] = photo_id
            res["quick"] = {k: (list(v) if isinstance(v, list) else v) for k, v in S.quick_answers(key).items()}
            S.record(res, keep=keep)
            st.session_state.results[key] = res
            st.rerun()
    st.caption("Your photo is checked in memory and never saved.")

    res = st.session_state.results.get(key)
    if res and res["photo"] == photo_id:
        _show_result(key, res)


def _bullets(items) -> str:
    return "<ul>" + "".join(f"<li>{ui.esc(x)}</li>" for x in items) + "</ul>"


def _show_result(key: str, res: dict) -> None:
    status = res["status"]
    doctor = S.CHECKS[key]["doctor"]
    info = S.info_for(key, res["label"])
    nxt = res["next"]
    ui.html('<div class="hc-h">3. Your result</div>')
    for warning in res["quality"]["warnings"]:
        st.warning(S.QUALITY_TEXT.get(warning, warning))

    _result_card(key, res)

    quick = res.get("quick") or {}
    why = list(nxt["reasons"])
    for line in S.triage.quick_lines(quick, key, S.risk_answers()):
        if line not in why:
            why.append(line)
    if why:
        ui.html(f'<div class="wc"><div class="k">Why this priority</div>{_bullets(why)}</div>')

    if status == "ok":
        ui.html(f'<div class="duo"><div class="g"><div class="k">What you can do</div>{_bullets(info["en"]["tips"])}</div>'
                f'<div class="r"><div class="k">See a doctor if</div>{_bullets(S.see_doctor_if(key))}</div></div>')
    else:
        ui.html(f'<div class="duo"><div class="r"><div class="k">See a doctor if</div>{_bullets(S.see_doctor_if(key))}</div></div>')

    _change(res)

    if res["heat"] is not None:
        ui.html('<div class="hc-h">Where the model looked</div>')
        with st.container(key="heatcard"):
            st.image(res["heat"])
            ui.html('<div class="legend"></div><div class="legend-l"><span>Less</span><span>More</span></div>'
                    '<p class="hc-muted" style="margin:8px 0 0 0">Bright areas influenced the result most. This explains the AI, '
                    'it is not a medical finding.</p>')

    ui.html('<div class="hc-h">Other possibilities</div>')
    rows = "".join(
        f'<div class="bar-row"><div class="t"><span>{ui.esc(S.pretty(p["label"]))}</span><span>{p["p"] * 100:.0f}%</span></div>'
        f'<div class="bar"><i style="width:{min(max(p["p"], 0.0), 1.0) * 100:.0f}%"></i></div></div>' for p in res["probs"][:4])
    ui.html(f'<div class="wc">{rows}</div>')

    if status != "invalid":
        _chat(key, res)

    st.link_button(f"Find a {doctor} near me", "https://www.google.com/maps/search/" + quote(f"{S.DOCTOR_SEARCH[doctor]} near me"),
                   icon=":material/location_on:", use_container_width=True)
    _feedback(key, res)


def _result_card(key: str, res: dict) -> None:
    status, label, prob = res["status"], res["label"], res["confidence"]
    nxt = res["next"]
    doctor = S.CHECKS[key]["doctor"]
    level = nxt["level"]
    if status == "ok":
        big, text = S.pretty(label), S.info_for(key, label)["en"]["about"]
    elif status == "uncertain":
        why = ("The photo quality is too low to trust a result." if res.get("demoted")
               else "The model is not confident about this photo.")
        big, text = "Not sure", f"{why} Best guess: {S.pretty(label)}."
    else:
        big, text = "Photo not suitable", "Please take a clear photo of the correct area and try again."
    pill = f"See a {doctor} soon" if level == "doctor" else nxt["title"]
    conf = (f'<span style="font-size:13px;color:#1B2A4A">{prob * 100:.0f}% confidence{" &#183; sample" if res.get("demo") else ""}</span>'
            if status != "invalid" else "")
    nxt_line = f'<div class="txt" style="margin-top:8px"><b>Next step:</b> {ui.esc(nxt["text"])}</div>' if level != "doctor" else ""
    ui.html(f'<div class="rc {level}"><div class="k">Screening result &#183; not a diagnosis</div><div class="big">{ui.esc(big)}</div>'
            f'<div class="row"><span class="chip">{ui.esc(pill)}</span>{conf}</div><div class="txt">{ui.esc(text)}</div>{nxt_line}</div>')


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
        msg = S.CHAT_ERRORS.get(out["error"], S.CHAT_ERRORS["unavailable"])
        if out.get("detail"):
            msg += f" (Technical detail: {out['detail']})"
        res["chat"].append(("err", msg))


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


def _thumb_b64(img) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _acne_entries(log: list) -> list:
    """Log entries with a date label. Sample points are spread weekly into the past, real ones use their own date."""
    ns = sum(1 for e in log if e.get("sample"))
    out, k = [], 0
    for n, e in enumerate(log):
        if e.get("sample"):
            label = (dt.date.today() - dt.timedelta(days=7 * (ns - k))).strftime("%d %b")
            k += 1
        else:
            label = e.get("date") or f"Check-in {n + 1}"
        out.append({"score": int(e["score"]), "sample": bool(e.get("sample")), "label": label, "thumb": e.get("thumb")})
    return out


def _photo_box(entry, fallback: str, tint: str) -> str:
    if entry and entry.get("thumb") is not None:
        return f'<div class="ph"><img src="{_thumb_b64(entry["thumb"])}" alt="Acne photo"></div>'
    return f'<div class="ph" style="background:{tint}">{ui.esc(fallback)}</div>'


def acne() -> None:
    ui.header("Acne tracker", "Add a photo and see how your skin changes")
    log = st.session_state.acne_log
    ents = _acne_entries(log)
    real = [e for e in ents if not e["sample"]]
    scores = [e["score"] for e in real]

    # The trend uses only the user's own check-ins. The sample points are just there to show the chart.
    if len(scores) >= 4:
        diff = sum(scores[-2:]) / 2 - sum(scores[:2]) / 2
    elif len(scores) >= 2:
        diff = scores[-1] - scores[0]
    else:
        diff = 0

    ui.html('<div class="hc-h">Add today\'s photo</div>')
    _source_tiles("acne")
    st.slider("How is your acne today? 0 is clear, 100 is severe", 0, 100, 40, key="acne_slider")
    st.checkbox("Keep this photo in my tracker so I can compare later", value=True, key="acne_keep")
    st.button("Save today's check-in", type="primary", key="acne_save", on_click=_save_acne, icon=":material/check:")
    st.caption("The level is your own rating. Aira does not grade acne from photos yet. Photos stay in this visit only.")

    # ---- result card
    if len(scores) < 2:
        status, bg, ink, arrow = "Add more check-ins", "#FFFFFF", "#274547", ""
        detail = ("The chart starts with sample points so you can see how it looks. Save your own check-ins above and "
                  "Aira will show your real trend." if not scores else "Save at least two check-ins to see your trend.")
    elif diff <= -5:
        status, bg, ink, arrow = "Improving", "#DDF3E6", "#14603A", ""
        detail = f"Down {abs(round(diff))} points since you started. Your routine seems to be working, keep going."
    elif diff >= 5:
        status, bg, ink, arrow = "Getting worse", "#FBE6DE", "#8A3A10", ""
        detail = (f"Up {round(diff)} points since you started. If it keeps rising, becomes painful or leaves marks, "
                  "please see a dermatologist.")
    else:
        status, bg, ink, arrow = "About the same", "#FFFFFF", "#274547", ""
        detail = "Your acne has stayed about the same. Keep the routine steady and check again next week."
    ui.html('<div class="hc-h">Your result</div>')
    cur = scores[-1] if scores else None
    score_html = (f'{cur}<span style="font-size:15px;font-weight:600"> /100 &#183; {_level(cur)}</span>' if cur is not None
                  else '<span style="font-size:20px;font-weight:700">No check-in yet</span>')
    last_delta = (f'{scores[-1] - scores[-2]:+d} points'.replace("-", "\u2212") if len(scores) >= 2 else "\u2014")
    ui.html(f'<div class="rc" style="background:#FAE5B5;border-color:#F0D9A0"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
            f'<div class="k" style="color:#6B4A00">Your acne level &#183; self-rated{"" if scores else " &#183; sample"}</div>'
            f'<span class="hc-pill" style="background:{bg};color:{ink}">{status}</span></div>'
            f'<div class="big">{score_html}</div><div class="txt">{detail}</div>'
            f'<div class="stat2"><div><div class="l">Since last check</div><div class="v">{last_delta}</div></div>'
            f'<div><div class="l">Check-ins saved</div><div class="v">{len(scores)}</div></div></div></div>')

    # ---- before and after
    ui.html('<div class="hc-h">Before and after</div>')
    first, last = (real[0], real[-1]) if len(real) >= 2 else (None, None)
    say = ""
    if first:
        d = last["score"] - first["score"]
        word = f"down {abs(d)} points" if d < 0 else f"up {d} points" if d > 0 else "about the same"
        say = f'<div class="aira-say">Aira: your level is {word} since {ui.esc(first["label"])}.</div>'
    ui.html('<div class="wc"><div class="ba">'
            f'<div>{_photo_box(first, "Your first photo", "#F8DCE8")}<div class="cap"><b>Before</b><span>{"Level " + str(first["score"]) if first else ""}</span></div></div>'
            f'<div>{_photo_box(last, "Today\'s photo", "#D5EBDD")}<div class="cap"><b>Now</b><span>{"Level " + str(last["score"]) if last else ""}</span></div></div>'
            f'</div>{say}</div>')

    # ---- weekly trend as bars
    shown = ents[-6:]
    if shown:
        top = max(max(e["score"] for e in shown), 1)
        bars = "".join(f'<div><i class="{"now" if n == len(shown) - 1 else ""}" style="height:{max(6, e["score"] / top * 100):.0f}%"></i>'
                       f'<span class="{"now" if n == len(shown) - 1 else ""}">{ui.esc("Today" if n == len(shown) - 1 and not e["sample"] else e["label"])}</span></div>'
                       for n, e in enumerate(shown))
        ui.html(f'<div class="hc-h">Weekly trend</div><div class="wc"><div class="trend">{bars}</div>'
                '<p class="hc-muted" style="margin:8px 0 0 0">Lower bars mean clearer skin.</p></div>')
    if any(e.get("sample") for e in log):
        st.caption("The first points are sample data so you can see how the tracker looks.")
        st.button("Clear sample data", key="clear_sample", on_click=_clear_sample)

    # ---- check-in list
    if ents:
        ui.html('<div class="hc-h">Check-ins</div>')
        tints = ["#D9EFE0", "#FAE5B5", "#E4E1F8"]
        for n in range(len(ents) - 1, -1, -1):
            e = ents[n]
            if e["sample"]:
                tag, tbg, tfg = "Sample", "#E6EAF2", "#46506A"
            else:
                prev = next((x for x in reversed(ents[:n]) if not x["sample"]), None)
                dlt = e["score"] - prev["score"] if prev else 0
                tag, tbg, tfg = (("First check-in", "#E6EAF2", "#46506A") if prev is None else
                                 ("Improving", "#DDF3E6", "#14603A") if dlt <= -5 else
                                 ("Getting worse", "#FBE6DE", "#8A3A10") if dlt >= 5 else ("About the same", "#E6EAF2", "#46506A"))
            ui.html(f'<div class="ci"><div class="ic" style="background:{tints[n % 3]}">&#128247;</div><div class="m"><b>{ui.esc(e["label"])}</b>'
                    f'<span>Acne level {e["score"]}</span></div><span class="hc-pill" style="background:{tbg};color:{tfg};font-size:12px">{tag}</span></div>')

    ui.card('<b>Aira\'s tip:</b> take each photo in the same light, at the same angle, without filters, '
            'so the weekly comparison stays fair.')


def _clear_sample() -> None:
    st.session_state.acne_log = [e for e in st.session_state.acne_log if not e.get("sample")]


def _save_acne() -> None:
    entry = {"score": int(st.session_state.acne_slider), "sample": False, "date": dt.date.today().strftime("%d %b"), "thumb": None}
    mode = st.session_state.get("srcmode_acne", "up")
    photo = st.session_state.get("up_acne" if mode == "up" else "cam_acne")
    if photo is not None and st.session_state.get("acne_keep", True):
        try:
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(photo.getvalue()))).convert("RGB")
            img.thumbnail((360, 360))
            entry["thumb"] = img
        except (OSError, ValueError):
            pass
    st.session_state.acne_log.append(entry)


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
