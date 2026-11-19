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
BENTO = {
    # key: (container class, colour, icon svg path content, title, subtitle, page, check key)
    "aira": ("#E4E1F8", "#5B4BC4", '<path d="M21 12a8 8 0 01-8 8H6l-3 3V12a8 8 0 018-8h2a8 8 0 018 8z"/>', "Talk with Aira", "Ask about your result", "aira", None),
    "skin": ("#FADDCF", "#B4531A", '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2.5 4 2.5S16 14 16 14M9 9.5h.01M15 9.5h.01"/>', "Skin check", "Acne, tinea, eczema", "check", "skin"),
    "oral": ("#DCE8B2", "#3D5A12", '<path d="M12 6C10 3 5 4 5 9c0 4 1.5 6 2.5 9 .5 2 2.5 2 3 0 .4-1.5 1.6-1.5 2 0 .5 2 2.5 2 3 0 1-3 2.5-5 2.5-9 0-5-5-6-5.5-3z"/>', "Oral check", "Gums, ulcers, teeth", "check", "oral"),
    "acne": ("#FAE5B5", "#8A5A00", '<path d="M3 7l6 6 4-4 8 8"/>', "Acne tracker", "Weekly progress", "acne", None),
    "sleep": ("#D5E4F5", "#1F4E8C", '<path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z"/>', "Sleep mode", "Sounds and timer", "sleep", None),
    "insomnia": ("#DCEDE5", "#0B6B45", '<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M9 9h6M9 13h6M9 17h3"/>', "Insomnia check", "5 quick questions", "insomnia", None),
    "tips": ("#F8DCE8", "#9B2C5E", '<path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0012 3z"/>', "Health tips", "News and care ideas", "tips", None),
}


def _tile(key: str, height: int) -> None:
    bg, fg, icon, title, sub, page, check_key = BENTO[key]
    with st.container(key=f"bt_{key}"):
        ui.html(
            f'<div class="bt-in" style="height:{height}px">'
            f'<div class="bt-ic"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{fg}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icon}</svg></div>'
            + ('<div class="bt-art" aria-hidden="true"><span style="background:#F2A88C"></span><span style="background:#9A8FE0"></span></div>' if key == "aira" else "")
            + f'<div><div class="bt-t">{title}</div><div class="bt-s">{sub}</div></div></div>'
        )
        kwargs = {"check_key": check_key} if check_key else {}
        st.button(f"Open {title}", key=f"tile_{key}", on_click=ui.go, args=(page,), kwargs=kwargs)


def home() -> None:
    name = st.session_state.get("name", "")
    ui.html(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin:4px 0 14px 0">
      <div><div class="hc-greet-a">{S.greeting()}</div><div class="hc-greet-b">{ui.esc(name) if name else "there"}</div></div>
      <div style="flex:none;width:64px;height:64px;border-radius:50%;background:#0B6665;display:flex;align-items:flex-end;justify-content:center;overflow:hidden">{ui.aira(60, suffix="hm")}</div>
    </div>
    """)
    left, right = st.columns(2)
    with left:
        _tile("aira", 290)
    with right:
        _tile("skin", 122)
        _tile("oral", 122)

    st.markdown("### Care")
    a, b = st.columns(2)
    with a:
        _tile("acne", 84)
    with b:
        _tile("sleep", 84)

    st.markdown("### Support")
    a, b = st.columns(2)
    with a:
        _tile("insomnia", 84)
    with b:
        _tile("tips", 84)
    st.markdown('<p class="hc-foot">AI screening only. See a doctor for a real diagnosis.</p>', unsafe_allow_html=True)


# ------------------------------------------------------------------ history
def history() -> None:
    st.markdown("# History")
    st.caption("Results from this visit. They are not stored after you close the app.")
    st.button("Open My Progress: trends, change alerts and your summary", icon=":material/timeline:", key="open_progress",
              on_click=ui.go, args=("progress",), type="primary")
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
