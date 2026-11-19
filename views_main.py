"""Login, home, history, profile and logout screens."""
import streamlit as st

import services as S
import ui
import views_care as vc


# ------------------------------------------------------------------ login
def login() -> None:
    ui.html(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:8px;margin:2.2rem 0 1.2rem 0;text-align:center">
      <div class="aira-float">{ui.logo(112)}</div>
      <h1 style="margin:0;color:#FFFFFF;font-size:2.1rem !important">Health Check</h1>
      <p style="margin:0 0 6px 0;font-size:16px;line-height:1.5;color:#E3F8EA">AI-Powered Health Screening</p>
    </div>
    """)
    # There are no accounts in this demo, so there is no password to type. Never ask for a real password
    # on a page that does not check it.
    with st.form("login_form"):
        name = st.text_input("Your name (optional)", placeholder="Your name (optional)", max_chars=30, label_visibility="collapsed")
        agree = st.checkbox("I understand Aira is a screening aid, not a doctor. It cannot diagnose.")
        submitted = st.form_submit_button("Continue as guest", type="primary")
    if submitted and not agree:
        st.error("Please tick the box to continue.")
    elif submitted:
        st.session_state.logged_in = True
        st.session_state.name = name.strip()
        st.session_state.page = "home"
        st.rerun()
    st.caption("Demo mode: no account is created. Your photo is checked in memory and is not saved on the server.")
    st.caption("AI screening only. It does not replace a doctor's diagnosis.")


# ------------------------------------------------------------------ home
def home() -> None:
    name = st.session_state.get("name", "")
    ui.html(f"""
    <div class="hc-top">
      <div><div class="hc-hello">Hello, {ui.esc(name) if name else "there"} &#128075;</div>
      <div class="hc-sub">Take care today, for a healthier tomorrow.</div></div>
      <div class="hc-avatar">{ui.esc((name[:1] or "G").upper())}</div>
    </div>
    """)
    with st.container(key="hero"):
        left, right = st.columns([3, 2])
        with left:
            ui.html('<div class="hero-t">Your Health,<br>Our Priority &#10084;&#65039;</div>'
                    '<div class="hero-s">AI Health Screening<br>for a Better You</div>')
            st.button("Start Scanning \u2192", key="hero_go", on_click=ui.go, args=("check",), kwargs={"check_key": "skin"})
        with right:
            ui.html(f'<div style="display:flex;justify-content:center;align-items:center;height:100%">{ui.shield(118)}</div>')

    st.markdown("### Categories")
    keys = list(S.CHECKS)
    for row in (keys[:2], keys[2:]):
        cols = st.columns(2)
        for col, key in zip(cols, row):
            cfg = S.CHECKS[key]
            ready = S.model_ready(key)
            with col, st.container(key=f"cat_{key}"):
                ui.html(f'<div class="cat-ic">{ui.ICONS[key]}</div><div class="cat-t">{ui.esc(cfg["title"])}</div>'
                        f'<div class="cat-s">{ui.esc(cfg["blurb"])}</div>')
                st.button("Scan Now \u2192" if ready else "Coming soon", key=f"tile_{key}", on_click=ui.go,
                          args=("check",), kwargs={"check_key": key}, disabled=not ready)

    with st.container(key="aihelp"):
        left, right = st.columns([3, 1.6])
        with left:
            ui.html(f'<div style="display:flex;gap:10px;align-items:center"><div style="flex:none">{ui.aira(46, suffix="ah")}</div>'
                    '<div><div class="ai-t">AI Help</div><div class="ai-s">Check first, then ask Aira.</div></div></div>')
        with right:
            st.button("Explore \u2192", key="aihelp_go", on_click=ui.go, args=("check",), kwargs={"check_key": "skin"})

    st.markdown("### Care and wellbeing")
    extras = [
        ("progress", "My Progress", ":material/timeline:"),
        ("acne", "Acne Tracker", ":material/trending_down:"),
        ("sleep", "Sleep Mode", ":material/bedtime:"),
        ("connect", "Feeling lonely?", ":material/favorite:"),
    ]
    for pair in (extras[:2], extras[2:]):
        cols = st.columns(2)
        for col, (page, title, icon) in zip(cols, pair):
            with col:
                st.button(title, icon=icon, key=f"extra_{page}", on_click=ui.go, args=(page,))

    st.markdown("### Health Tips")
    ui.card('<div class="tip-row"><svg width="34" height="34" viewBox="0 0 40 40" style="flex:none"><path d="M20 3L35 9V20C35 29 28 35 20 38C12 35 5 29 5 20V9Z" fill="#17A34A"/>'
            '<path d="M12 20l6 6 11-12" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            f'<div><div class="t">Tip of the day</div><div class="s">{ui.esc(S.daily_tip())}</div></div></div>')
    st.caption("AI screening only. See a doctor for a real diagnosis.")


# ------------------------------------------------------------------ history
def history() -> None:
    st.markdown("# History")
    st.caption("Results from this visit. They are not stored after you close the app.")
    entries = st.session_state.get("history", [])
    for e in reversed(entries):
        if e["status"] == "ok":
            title, note = S.pretty(e["label"]), f'{e["confidence"] * 100:.0f}% confidence'
        elif e["status"] == "uncertain":
            title, note = "Not sure", f'Best guess {S.pretty(e["label"])} ({e["confidence"] * 100:.0f}%)'
        else:
            title, note = "Photo not suitable", "Please retake the photo"
        ui.card(
            f'<div style="font-size:12px;font-weight:700" class="hc-muted">{ui.esc(S.CHECKS[e["check"]]["title"].upper())}'
            f' &#183; {ui.esc(e["time"])}</div>'
            f'<div style="font-size:18px;font-weight:800">{ui.esc(title)}</div>'
            f'<div class="hc-muted">{ui.esc(note)}</div>'
        )
    log = st.session_state.get("acne_log", [])
    real = [e for e in log if not e.get("sample")]
    if real:
        ui.card(
            '<div style="font-size:12px;font-weight:700" class="hc-muted">ACNE TRACKER</div>'
            f'<div style="font-size:18px;font-weight:800">{len(real)} check-ins saved</div>'
            f'<div class="hc-muted">Latest score {real[-1]["score"]} out of 100</div>'
        )
    if not entries and not real:
        ui.card('<div style="font-weight:700">Nothing here yet</div>'
                '<div class="hc-muted">Run a check and your results will show up here during this visit.</div>')


# ------------------------------------------------------------------ profile
def profile() -> None:
    st.markdown("# Profile")
    name = st.session_state.get("name", "") or "Guest"
    ui.card(
        '<div class="hc-muted">Name</div>'
        f'<div style="font-weight:700;margin-bottom:10px">{ui.esc(name)}</div>'
        '<div class="hc-muted">Account</div>'
        '<div style="font-weight:700;margin-bottom:10px">Guest session (no account)</div>'
        '<div class="hc-muted">Your photos</div>'
        '<div style="font-weight:700">Checked in memory, never saved</div>'
    )
    ui.card('<b>About your data</b><div class="hc-muted" style="margin-top:2px">'
            'Only the text of a result and your chat messages go to Google Gemini when you chat with Aira. '
            'Your photo is never sent. Feedback saves only your answer and comment, no photo and no name.</div>')
    st.markdown("### Risk factors (optional)")
    vc.risk_form("profile")
    st.markdown("### Your data")
    ui.card("<b>Your control</b><div class=\"hc-muted\" style=\"margin-top:2px\">Photos are checked in memory and never saved. "
            "Results and answers stay in this visit only. You can download a progress file to keep, and delete everything here "
            "at any time. Feedback you send has no photo and no name, so it cannot be linked back to you.</div>")
    if not st.session_state.get("confirm_delete"):
        st.button("Delete all my data", icon=":material/delete:", key="ask_delete",
                  on_click=lambda: st.session_state.update(confirm_delete=True))
    else:
        st.warning("This clears your results, answers and chats from this visit.")
        st.button("Yes, delete everything", type="primary", key="do_delete", on_click=_wipe)
        st.button("Cancel", key="cancel_delete", on_click=lambda: st.session_state.update(confirm_delete=False))
    st.caption("AI screening only. It does not replace a doctor's diagnosis.")


def _wipe() -> None:
    st.session_state.results = {}
    st.session_state.history = []
    st.session_state.risk = dict(S.triage.DEFAULT_RISK)
    st.session_state.acne_log = []
    st.session_state.confirm_delete = False


# ------------------------------------------------------------------ logout
def _do_logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def logout() -> None:
    ui.html(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:12px;margin:2rem 0 1rem 0;text-align:center">
      {ui.aira(110, sleepy=True, suffix="o")}
      <h1 style="margin:0">Log out?</h1>
      <p class="hc-muted" style="margin:0;font-size:15px">Your results and chats from this visit will be cleared.</p>
    </div>
    """)
    st.button("Yes, log out", type="primary", key="do_logout", on_click=_do_logout)
    st.button("Cancel", key="cancel_logout", on_click=ui.go, args=("home",))
