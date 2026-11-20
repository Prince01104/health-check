"""Login, home, history, profile and logout screens."""
import streamlit as st

import services as S
import ui
import views_care as vc


# ------------------------------------------------------------------ login
def login() -> None:
    chips = "".join(f'<span style="background:{bg};color:{fg}">{t}</span>' for t, bg, fg in (
        ("Skin", "#FADDCF", "#8A3A1E"), ("Oral", "#DCE8B2", "#4A5A12"), ("Sleep", "#D5E4F5", "#1F4E86"), ("Acne", "#FAE5B5", "#7A5200")))
    ui.html(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:6px;margin:1.2rem 0 0 0;text-align:center">
      <div class="aira-float">{ui.aira(150, suffix="l")}</div>
      <h1 style="margin:6px 0 0 0;font-size:2.3rem !important;color:#1B2A4A">Hi, I am Aira</h1>
      <p style="margin:0 0 4px 0;font-size:17px;line-height:1.5;color:#5B6478">Your AI health companion.<br>Skin, teeth, sleep and more.</p>
    </div>
    <div class="lg-chips">{chips}</div>
    """)
    # Demo only: nothing is checked or stored. The password box is there for the look of a real login and is thrown away.
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com", max_chars=60)
        st.text_input("Password", placeholder="Enter your password", type="password", max_chars=60)
        agree = st.checkbox("I understand Aira is a screening aid, not a doctor. It cannot diagnose.")
        submitted = st.form_submit_button("Login", type="primary")
    if submitted and not agree:
        st.error("Please tick the box to continue.")
    elif submitted:
        first = "".join(ch for ch in email.split("@")[0].split(".")[0] if ch.isalpha())[:20].title()
        st.session_state.logged_in = True
        st.session_state.name = first
        st.session_state.page = "home"
        st.rerun()
    st.caption("Demo mode: any email and password works. Nothing is saved, and your photo is checked in memory only.")
    st.caption("AI screening only. It does not replace a doctor's diagnosis.")


# ------------------------------------------------------------------ home
def _svg(path: str, color: str, size: int = 24) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>')


ICON = {
    "skin": ('<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2.5 4 2.5S16 14 16 14M9 9.5h.01M15 9.5h.01"/>', "#B4531A"),
    "oral": ('<path d="M12 6C10 3 5 4 5 9c0 4 1.5 6 2.5 9 .5 2 2.5 2 3 0 .4-1.5 1.6-1.5 2 0 .5 2 2.5 2 3 0 1-3 2.5-5 2.5-9 0-5-5-6-5.5-3z"/>', "#1F5A3A"),
    "acne": ('<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>', "#6B4A00"),
    "sleep": ('<path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z"/>', "#4B3FB0"),
    "insomnia": ('<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M9 9h6M9 13h6M9 17h3"/>', "#1F4E8C"),
    "aira": ('<rect x="5" y="8" width="14" height="11" rx="4"/><path d="M12 8V5M9.5 13h.01M14.5 13h.01M10 16h4"/><circle cx="12" cy="4" r="1"/>', "#9B2C5E"),
    "nail": ('<path d="M8 20v-9a4 4 0 018 0v9"/><path d="M8 20h8"/>', "#4A5A7A"),
    "infection": ('<circle cx="12" cy="12" r="4"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>', "#4A5A7A"),
    "bulb": ('<path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0012 3z"/>', "#4B3FB0"),
    "news": ('<path d="M4 5h13a2 2 0 012 2v12H6a2 2 0 01-2-2z"/><path d="M8 9h7M8 13h7M8 16h4"/>', "#4B3FB0"),
}
ARROW_UP = '<path d="M7 17L17 7M9 7h8v8"/>'
CHEVRON = '<path d="M9 6l6 6-6 6"/>'


def _go_card(key: str, inner: str, page: str, label: str, check_key: str | None = None) -> None:
    """A tappable card: the HTML is the look, an invisible full-size button on top does the tap."""
    with st.container(key=f"hm_{key}"):
        ui.html(inner)
        kwargs = {"check_key": check_key} if check_key else {}
        st.button(f"Open {label}", key=f"tile_{key}", on_click=ui.go, args=(page,), kwargs=kwargs)


def _icon(name: str) -> str:
    path, color = ICON[name]
    return f'<div class="hm-ic">{_svg(path, color)}</div>'


def _big_tile(key: str, title: str, sub: str) -> None:
    inner = (f'<div class="hm-in" style="height:168px;justify-content:space-between">'
             f'<div style="display:flex;justify-content:space-between;align-items:flex-start">{_icon(key)}'
             f'<div class="hm-circ">{_svg(ARROW_UP, "#1B2A4A", 16)}</div></div>'
             f'<div><div class="hm-t">{title}</div><div class="hm-s">{sub}</div></div></div>')
    _go_card(key, inner, "check", title, key)


def _row(key: str, bg: str, title: str, sub: str, page: str) -> None:
    inner = (f'<div class="hm-in" style="flex-direction:row;align-items:center;gap:14px;padding:12px 16px">'
             f'<div class="hm-ic" style="background:{bg}">{_svg(*ICON[key])}</div>'
             f'<div style="flex:1;min-width:0"><div class="hm-t" style="font-size:17px">{title}</div><div class="hm-s">{sub}</div></div>'
             f'{_svg(CHEVRON, "#1B2A4A", 20)}</div>')
    _go_card(key, inner, page, title)


def _soon(key: str, title: str) -> str:
    return (f'<div class="hm-soon">{_icon(key)}<div><div class="hm-t" style="font-size:16px">{title}</div>'
            f'<span class="hm-pill">Coming soon</span></div></div>')


def home() -> None:
    name = st.session_state.get("name", "")
    ui.html(f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin:2px 0 10px 0">
      <div><div class="hc-greet-a">{S.greeting()}</div><div class="hc-greet-b">{ui.esc(name) if name else "there"}</div>
      <div class="hm-s" style="margin-top:2px">How are you feeling today?</div></div>
      <div style="position:relative;flex:none;width:64px;height:64px">
        <div style="width:64px;height:64px;border-radius:50%;background:#0B6665;border:3px solid #fff;box-sizing:border-box;display:flex;align-items:flex-end;justify-content:center;overflow:hidden">{ui.aira(58, suffix="hm")}</div>
        <span style="position:absolute;right:2px;bottom:4px;width:14px;height:14px;border-radius:50%;background:#2DB35D;border:2px solid #fff"></span></div>
    </div>
    """)

    # ---- Health news (top story if a feed works, otherwise the tip of the day)
    with st.container(key="newshead"):
        ui.html('<div class="hm-h" style="margin:8px 0">Health news</div>')
        st.button("See all", key="seeall", on_click=ui.go, args=("tips",))
    items = S.health_news()
    if items:
        tag, title = "TOP STORY", items[0]["title"]
        sub = ui.esc(items[0]["source"]) + (f" &#183; {ui.esc(items[0]['ago'])}" if items[0]["ago"] else "")
        icon = "news"
    else:
        tag, title, sub, icon = "TIP OF THE DAY", S.daily_tip(), "Tap for more health tips", "bulb"
        sub = ui.esc(sub)
    shown = title if len(title) <= 95 else title[:92].rsplit(" ", 1)[0] + "..."
    inner = (f'<div class="hm-in" style="flex-direction:row;gap:12px;align-items:flex-start">'
             f'<div style="flex:1;min-width:0"><span class="hm-tag">{tag}</span>'
             f'<div class="hm-t" style="font-size:21px;margin-top:10px">{ui.esc(shown)}</div>'
             f'<div class="hm-s" style="margin-top:6px">{sub}</div></div>{_icon(icon)}</div>')
    _go_card("news", inner, "tips", "health news")

    # ---- Quick checks
    ui.html('<div class="hm-h">Quick checks</div>')
    left, right = st.columns(2)
    with left:
        _big_tile("skin", "Skin check", "Acne, tinea, eczema")
    with right:
        _big_tile("oral", "Oral check", "Gums, ulcers, teeth")
    inner = (f'<div class="hm-in" style="flex-direction:row;align-items:center;gap:14px;padding:16px">{_icon("acne")}'
             f'<div style="flex:1;min-width:0"><div class="hm-t" style="font-size:21px">Acne tracker</div>'
             f'<div class="hm-s">Add photos, see how acne changes</div></div>'
             f'<div class="hm-circ">{_svg(CHEVRON, "#1B2A4A", 18)}</div></div>')
    _go_card("acne", inner, "acne", "Acne tracker")
    a, b = st.columns(2)
    a.markdown(_soon("nail", "Nail check"), unsafe_allow_html=True)
    b.markdown(_soon("infection", "Infection check"), unsafe_allow_html=True)

    # ---- Care and wellbeing
    ui.html('<div class="hm-h">Care and wellbeing</div>')
    _row("sleep", "#E4E1F8", "Sleep sounds", "4 calming sounds with a timer", "sleep")
    _row("insomnia", "#DCE8F8", "Insomnia check", "5 quick questions and ideas", "insomnia")
    _row("aira", "#F8DCE8", "Talk with Aira", "Ask any health question", "aira")
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
    st.session_state.quick = {}
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
