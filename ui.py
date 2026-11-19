"""Shared styling and small UI helpers for the Health Check app."""
import html as _html

import streamlit as st

FONT_URL = (
    "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:"
    "wght@400;500;600;700;800&display=swap"
)

# ---------------------------------------------------------------- CSS
BASE_CSS = """
@import url('__FONT__');
html, body, .stApp, button, input, textarea, select {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
}
#MainMenu, footer, [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], [data-testid="stDecoration"] { display: none !important; }
.block-container {
  max-width: 430px !important;
  padding: 1.4rem 1.1rem 7rem 1.1rem !important;
  position: relative; z-index: 1;
}
h1, h2, h3 { letter-spacing: -0.02em; font-weight: 800 !important; }
h1 { font-size: 1.7rem !important; padding: 0.2rem 0 0.4rem 0 !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
.stButton, [data-testid="stFormSubmitButton"] { width: 100%; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  width: 100%; border-radius: 999px !important; min-height: 50px;
  font-weight: 700 !important; font-size: 15px !important;
}
[data-testid="stImage"] img, [data-testid="stCameraInput"] video { border-radius: 16px; width: 100%; }
.hc-card { border-radius: 22px; padding: 16px; margin: 0 0 12px 0; }
.hc-pill { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 800; }
.hc-muted { font-size: 13px; line-height: 1.5; }
.hc-step { display: flex; gap: 14px; align-items: flex-start; padding: 14px; border-radius: 18px; margin: 0 0 10px 0; }
.hc-num { width: 36px; height: 36px; border-radius: 18px; display: flex; align-items: center;
  justify-content: center; font-size: 15px; font-weight: 800; flex: none; }
@keyframes floaty { 0% {transform: translateY(0)} 50% {transform: translateY(-10px)} 100% {transform: translateY(0)} }
@keyframes blink { 0%,92%,100% {transform: scaleY(1)} 96% {transform: scaleY(0.1)} }
@keyframes pulse { 0% {opacity: .35} 50% {opacity: 1} 100% {opacity: .35} }
@keyframes drift1 { 0% {transform: translate(0,0) scale(1)} 50% {transform: translate(60px,90px) scale(1.25)} 100% {transform: translate(0,0) scale(1)} }
@keyframes drift2 { 0% {transform: translate(0,0) scale(1.1)} 50% {transform: translate(-80px,-60px) scale(0.9)} 100% {transform: translate(0,0) scale(1.1)} }
.aira-float { animation: floaty 5s ease-in-out infinite; }
.aira-eye { animation: blink 5s infinite; transform-box: fill-box; transform-origin: center; }
.aira-pulse { animation: pulse 2.4s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .aira-float, .aira-eye, .aira-pulse, .hc-blob { animation: none !important; }
}
/* bottom navigation */
.st-key-bottomnav {
  position: fixed; left: 50%; transform: translateX(-50%); bottom: 0;
  width: min(430px, 100%); z-index: 999; padding: 6px 10px 10px 10px;
}
.st-key-bottomnav button {
  background: transparent !important; border: none !important; box-shadow: none !important;
  min-height: 56px; font-size: 12px !important; font-weight: 600 !important; padding: 0 !important;
}
.st-key-bottomnav [data-testid="stHorizontalBlock"] { gap: 0.2rem; }
/* Streamlit stacks columns on small screens. This app is a phone layout, so keep columns side by side. */
[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"], [data-testid="stHorizontalBlock"] > [data-testid="column"] {
  min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;
}
"""

LIGHT_CSS = """
.stApp { background: #F4FBF6 !important; }
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"] { color: #10281A; }
.stApp [data-testid="stCaptionContainer"] { color: #4A6455; }
h3 { font-size: 1.15rem !important; margin-top: .6rem !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  background: #FFFFFF; border: 1.5px solid #CFE8D6; color: #0B7A36;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { border-color: #17A34A; color: #0B7A36; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg, #17A34A, #0B7A36) !important; border: none !important;
  box-shadow: 0 6px 16px rgba(11,122,54,.28);
}
.stButton > button[kind="primary"] *, button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primaryFormSubmit"] * { color: #FFFFFF !important; }
.hc-card { background: #FFFFFF; border: 1.5px solid #DCEFE1; box-shadow: 0 6px 18px rgba(16,80,40,.06); }
.hc-muted { color: #4A6455; }
.hc-step.on { background: #FFFFFF; border: 2px solid #17A34A; }
.hc-step.off { background: #EAF3EC; border: 1.5px solid #DCEFE1; }
.hc-step.done { background: #FFFFFF; border: 1.5px solid #14603A; }
.hc-num { background: #CFE5D5; color: #25432F; }
.hc-step.on .hc-num { background: #17A34A; color: #FFFFFF; }
.hc-step.done .hc-num { background: #DDF3E6; color: #14603A; }

/* floating bottom navigation */
.st-key-bottomnav {
  background: #FFFFFF; border: 1px solid #DCEFE1; border-radius: 26px; bottom: 10px !important;
  box-shadow: 0 10px 30px rgba(16,80,40,.16); width: min(400px, calc(100% - 20px)) !important;
}
.st-key-bottomnav button { color: #4A6455 !important; border-radius: 20px !important; }
.st-key-bottomnav button[kind="primary"], .st-key-bottomnav button[data-testid="stBaseButton-primary"] {
  background: #E3F6E8 !important; box-shadow: none !important; color: #0B7A36 !important;
}
.st-key-bottomnav button[kind="primary"] *, .st-key-bottomnav button[data-testid="stBaseButton-primary"] * { color: #0B7A36 !important; }

/* home */
.hc-top { display: flex; align-items: center; justify-content: space-between; margin: 0 0 12px 0; }
.hc-hello { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; }
.hc-sub { font-size: 13px; color: #4A6455; margin-top: 2px; }
.hc-avatar { width: 46px; height: 46px; border-radius: 50%; background: linear-gradient(135deg,#34C759,#0B7A36); color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 19px; flex: none; }
.st-key-hero { background: linear-gradient(135deg, #17A34A 0%, #0B7A36 100%); border-radius: 26px; padding: 18px 8px 16px 18px;
  margin: 0 0 14px 0; box-shadow: 0 12px 28px rgba(11,122,54,.30); overflow: hidden; }
.st-key-hero * { color: #FFFFFF; }
.hero-t { font-size: 22px; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; }
.hero-s { font-size: 13px; margin: 8px 0 12px 0; line-height: 1.4; opacity: .95; }
.st-key-hero button { background: #FFFFFF !important; border: none !important; min-height: 40px !important; width: auto !important;
  padding: 0 14px !important; box-shadow: none !important; }
.st-key-hero button * { color: #0B7A36 !important; font-weight: 800 !important; font-size: 13px !important; }
.st-key-hero .stButton { width: auto; }
.cat-ic { height: 58px; display: flex; align-items: center; justify-content: center; margin-bottom: 6px; }
.cat-t { font-size: 16px; font-weight: 800; text-align: center; }
.cat-s { font-size: 12px; text-align: center; color: #4A6455; margin: 2px 0 10px 0; }
[class*="st-key-cat_"] { border-radius: 22px; padding: 14px 10px 10px 10px; }
[class*="st-key-cat_"] button { min-height: 40px !important; background: rgba(255,255,255,.75) !important; border: none !important;
  box-shadow: none !important; }
[class*="st-key-cat_"] button * { font-size: 13px !important; font-weight: 800 !important; }
.st-key-cat_skin { background: #DDF5E3; } .st-key-cat_oral { background: #DCEFFD; }
.st-key-cat_infection, .st-key-cat_nail { background: #EEF2EF; }
.st-key-cat_infection button *, .st-key-cat_nail button * { color: #7B8A80 !important; }
.st-key-aihelp { background: #ECE6FF; border-radius: 22px; padding: 14px 14px 18px 14px; margin: 6px 0 12px 0; }
.st-key-aihelp button { background: #FFFFFF !important; border: none !important; min-height: 38px !important; }
.st-key-aihelp button * { color: #4B2BC4 !important; font-weight: 800 !important; font-size: 13px !important; }
.ai-t { font-size: 16px; font-weight: 800; color: #1E1450; } .ai-s { font-size: 12px; color: #4A4170; line-height: 1.4; }
.tip-row { display: flex; gap: 12px; align-items: center; }
.tip-row .t { font-weight: 800; font-size: 14px; } .tip-row .s { font-size: 13px; color: #4A6455; line-height: 1.4; }
[class*="st-key-extra_"], [class*="st-key-extra_"] .stButton, [class*="st-key-cat_"] .stButton { width: 100% !important; }
[class*="st-key-extra_"] button, [class*="st-key-cat_"] button { width: 100% !important; }
[class*="st-key-extra_"] button { min-height: 46px !important; font-size: 13px !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }

/* check page */
.hc-banner { border-radius: 24px; margin: 0 0 12px 0; overflow: hidden; line-height: 0; }
[data-testid="stFileUploaderDropzone"] { border: 2px dashed #9FD4AE !important; border-radius: 22px !important; background: #FFFFFF !important;
  padding: 22px 14px !important; }
[data-testid="stFileUploaderDropzone"] button { background: linear-gradient(135deg,#17A34A,#0B7A36) !important; border: none !important;
  border-radius: 999px !important; min-height: 44px !important; padding: 0 22px !important; }
[data-testid="stFileUploaderDropzone"] button * { color: #FFFFFF !important; font-weight: 800 !important; }
.hc-secure { display: flex; gap: 12px; align-items: center; background: #DDF5E3; border-radius: 18px; padding: 12px 14px;
  font-size: 13px; line-height: 1.4; margin: 0 0 12px 0; }
[data-testid="stExpander"] { border: 1.5px solid #DCEFE1 !important; border-radius: 18px !important; background: #FFFFFF; }
[data-testid="stProgress"] > div > div > div > div { background-color: #17A34A !important; }
"""

DARK_CSS = """
.stApp { background: linear-gradient(180deg, #0A1030 0%, #121A4A 100%) !important; }
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp span,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"] p { color: #EAF0FF; }
.stApp [data-testid="stCaptionContainer"] { color: #B8C8FF; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  background: rgba(255,255,255,0.09); border: 1.5px solid rgba(255,255,255,0.24); color: #EAF0FF;
}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: #A9BCFF !important; border: 1.5px solid #A9BCFF !important;
}
.stButton > button[kind="primary"] *, button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primaryFormSubmit"] * { color: #0A1030 !important; font-weight: 800; }
.hc-card { background: rgba(255,255,255,0.09); border: 1.5px solid rgba(255,255,255,0.18); }
.hc-muted { color: #C5D0F5; }
"""

LOGIN_CSS = """
.stApp { background: linear-gradient(160deg, #3BD16F 0%, #17A34A 45%, #0B7A36 100%) !important; }
.stApp::before {
  content: ""; position: fixed; right: -90px; top: -70px; width: 300px; height: 300px; border-radius: 50%;
  background: rgba(255,255,255,.16); z-index: 0;
}
.stApp::after {
  content: ""; position: fixed; left: -120px; bottom: -110px; width: 340px; height: 340px; border-radius: 50%;
  background: rgba(255,255,255,.12); z-index: 0;
}
.stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp span,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] p { color: #FFFFFF; }
.stApp [data-testid="stCaptionContainer"] { color: #E3F8EA; }
[data-baseweb="base-input"], [data-baseweb="input"] { background: rgba(255,255,255,0.20) !important; border-radius: 999px !important; }
[data-baseweb="input"] { border: 1.5px solid rgba(255,255,255,0.55) !important; }
[data-baseweb="base-input"] input { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; background: transparent !important;
  padding-left: 18px !important; }
[data-baseweb="base-input"] input::placeholder { color: #E3F8EA !important; -webkit-text-fill-color: #E3F8EA !important; opacity: 1; }
[data-testid="stTextInputRootElement"], [data-testid="stTextInputRootElement"] > div { background: rgba(255,255,255,0.22) !important;
  border-radius: 999px !important; border: 1.5px solid rgba(255,255,255,0.6) !important; }
[data-testid="stTextInputRootElement"] input { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; padding-left: 18px !important; }
[data-testid="stTextInputRootElement"] input::placeholder { color: #E3F8EA !important; -webkit-text-fill-color: #E3F8EA !important; opacity: 1; }
[data-testid="stCheckbox"] label span { color: #FFFFFF !important; font-size: 13px; }
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child { background: rgba(255,255,255,.25) !important; border-color: #FFFFFF !important; }
[data-testid="stFormSubmitButton"] > button { background: #FFFFFF !important; border: none !important; box-shadow: 0 8px 20px rgba(0,0,0,.16); }
[data-testid="stFormSubmitButton"] > button * { color: #0B7A36 !important; font-weight: 800; }
[data-testid="stAlert"] { background: rgba(255,255,255,.92) !important; border-radius: 16px; }
[data-testid="stAlert"] * { color: #8A1C14 !important; }
"""


def inject(theme: str) -> None:
    """Inject CSS for the given theme: 'light', 'dark' or 'login'."""
    parts = [BASE_CSS.replace("__FONT__", FONT_URL)]
    parts.append({"light": LIGHT_CSS, "dark": DARK_CSS, "login": LOGIN_CSS}[theme])
    st.markdown("<style>" + "\n".join(parts) + "</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def esc(text) -> str:
    """Escape user-typed text before it goes into HTML (the name field, for example)."""
    return _html.escape(str(text), quote=True)


def html(markup: str) -> None:
    """Render HTML. Leading spaces are stripped so Markdown never turns it into a code block."""
    flat = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(flat, unsafe_allow_html=True)


def card(inner: str, extra_style: str = "") -> None:
    html(f'<div class="hc-card" style="{extra_style}">{inner}</div>')


def go(page: str, **state) -> None:
    """Button callback: switch page and optionally set session values."""
    st.session_state.page = page
    for key, value in state.items():
        st.session_state[key] = value


def back_button(target: str = "home", label: str = "Back") -> None:
    st.button(label, icon=":material/arrow_back:", key=f"back_{target}_{label}", on_click=go, args=(target,))


def aira(size: int = 150, sleepy: bool = False, suffix: str = "a") -> str:
    """Aira, the original humanoid guide, as inline SVG."""
    eyes = (
        '<path d="M45 56q5 4 10 0M65 56q5 4 10 0" fill="none" stroke="#7CF2E0" stroke-width="2.4" stroke-linecap="round"/>'
        if sleepy
        else '<ellipse class="aira-eye" cx="50" cy="56" rx="4" ry="5" fill="#7CF2E0"/>'
             '<ellipse class="aira-eye" cx="70" cy="56" rx="4" ry="5" fill="#7CF2E0"/>'
    )
    h = round(size * 140 / 120)
    return (
        f'<svg width="{size}" height="{h}" viewBox="0 0 120 140" role="img" aria-label="Aira, your AI health companion">'
        f'<defs><linearGradient id="b{suffix}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2FD3C0"/>'
        f'<stop offset="1" stop-color="#127A8C"/></linearGradient>'
        f'<linearGradient id="h{suffix}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F2FBFA"/>'
        f'<stop offset="1" stop-color="#BFE6E2"/></linearGradient></defs>'
        f'<path d="M18 140C18 108 38 96 60 96C82 96 102 108 102 140Z" fill="url(#b{suffix})"/>'
        '<rect x="52" y="82" width="16" height="18" rx="6" fill="#7BCFC6"/>'
        '<circle cx="28" cy="56" r="7" fill="#2FD3C0"/><circle cx="92" cy="56" r="7" fill="#2FD3C0"/>'
        f'<rect x="30" y="20" width="60" height="68" rx="28" fill="url(#h{suffix})"/>'
        '<path d="M34 40C34 22 86 22 86 40Z" fill="#2FD3C0"/>'
        '<rect x="38" y="42" width="44" height="32" rx="16" fill="#0B2B33"/>'
        + eyes +
        '<path d="M52 65Q60 71 68 65" fill="none" stroke="#7CF2E0" stroke-width="2.2" stroke-linecap="round"/>'
        '<circle class="aira-pulse" cx="60" cy="118" r="5" fill="#E8FFFB"/>'
        '<path d="M52 118h4l2-4 3 8 2-4h5" fill="none" stroke="#127A8C" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )


LOGO_SVG = (
    '<svg width="{s}" height="{s}" viewBox="0 0 120 120" role="img" aria-label="Health Check logo">'
    '<path d="M60 104C28 82 12 62 12 42C12 28 23 18 36 18C46 18 55 23 60 32C65 23 74 18 84 18C97 18 108 28 108 42C108 62 92 82 60 104Z" fill="#FFFFFF"/>'
    '<rect x="50" y="36" width="20" height="46" rx="5" fill="#17A34A"/><rect x="37" y="49" width="46" height="20" rx="5" fill="#17A34A"/>'
    '<path d="M84 98C96 92 104 80 102 66C94 70 86 78 84 98Z" fill="#CFF5DA" stroke="#17A34A" stroke-width="3"/></svg>'
)


def logo(size: int = 120) -> str:
    return LOGO_SVG.replace("{s}", str(size))


def shield(size: int = 110) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" role="img" aria-label="Health shield">'
        '<path d="M58 12L98 26V58C98 82 82 98 58 108C34 98 18 82 18 58V26Z" fill="#D8F8E2" stroke="#FFFFFF" stroke-width="4"/>'
        '<path d="M58 22L88 32V58C88 76 76 89 58 97C40 89 28 76 28 58V32Z" fill="#2ED86A"/>'
        '<rect x="52" y="40" width="12" height="36" rx="3" fill="#FFFFFF"/><rect x="40" y="52" width="36" height="12" rx="3" fill="#FFFFFF"/>'
        '<path d="M92 40C108 44 112 64 100 82" fill="none" stroke="#0A3D22" stroke-width="4" stroke-linecap="round"/>'
        '<circle cx="98" cy="88" r="8" fill="#FFFFFF" stroke="#0A3D22" stroke-width="3"/></svg>'
    )


ICONS = {
    "skin": ('<svg width="54" height="54" viewBox="0 0 60 60"><rect x="6" y="14" width="48" height="36" rx="10" fill="#FF9E85"/>'
             '<circle cx="20" cy="30" r="2.6" fill="#D9573C"/><circle cx="32" cy="24" r="2.6" fill="#D9573C"/>'
             '<circle cx="40" cy="36" r="2.6" fill="#D9573C"/><circle cx="26" cy="40" r="2.6" fill="#D9573C"/>'
             '<path d="M36 16C38 8 42 4 46 2" stroke="#2B2B2B" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>'),
    "oral": ('<svg width="54" height="54" viewBox="0 0 60 60"><path d="M30 10C24 4 12 6 12 20C12 30 16 36 18 46C19 52 24 52 26 46C28 40 32 40 34 46C36 52 41 52 42 46C44 36 48 30 48 20C48 6 36 4 30 10Z" '
             'fill="#FFFFFF" stroke="#4DA3E8" stroke-width="3" stroke-linejoin="round"/></svg>'),
    "infection": ('<svg width="54" height="54" viewBox="0 0 60 60"><circle cx="30" cy="30" r="14" fill="#C9D3CC"/>'
                  '<g stroke="#C9D3CC" stroke-width="4" stroke-linecap="round"><path d="M30 6v8M30 46v8M6 30h8M46 30h8M13 13l6 6M41 41l6 6M47 13l-6 6M19 41l-6 6"/></g></svg>'),
    "nail": ('<svg width="54" height="54" viewBox="0 0 60 60"><path d="M18 52V26a4 4 0 018 0V14a4 4 0 018 0v10a4 4 0 018 0v6a4 4 0 018 0v14c0 6-6 10-14 10H28c-6 0-10-4-10-8Z" fill="#C9D3CC"/></svg>'),
}


def banner(kind: str = "skin") -> None:
    """Friendly header picture for a check page: a scan frame next to a simple doctor figure."""
    patch = "#E8A48C" if kind == "skin" else "#F7F7F7"
    html(
        '<div class="hc-banner"><svg width="100%" viewBox="0 0 400 170" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Scan frame and a doctor">'
        '<defs><linearGradient id="bn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C8F5D6"/><stop offset="1" stop-color="#7EDC9C"/></linearGradient></defs>'
        '<rect width="400" height="170" fill="url(#bn)"/><circle cx="360" cy="20" r="70" fill="#FFFFFF" opacity=".25"/>'
        f'<rect x="38" y="30" width="130" height="110" rx="16" fill="{patch}"/><circle cx="108" cy="82" r="4" fill="#8C3B2A"/>'
        '<path d="M30 52V38a8 8 0 018-8h14M154 30h14a8 8 0 018 8v14M176 118v14a8 8 0 01-8 8h-14M52 140H38a8 8 0 01-8-8v-14" '
        'fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M236 170C236 130 262 118 296 118C330 118 356 130 356 170Z" fill="#FFFFFF"/>'
        '<path d="M278 120L296 150L314 120" fill="#4DA3E8"/>'
        '<path d="M268 126C262 146 270 158 284 158" fill="none" stroke="#5B6B7A" stroke-width="3"/><circle cx="286" cy="158" r="5" fill="#5B6B7A"/>'
        '<rect x="286" y="100" width="20" height="22" rx="8" fill="#F2C3A5"/>'
        '<ellipse cx="296" cy="84" rx="30" ry="34" fill="#F7D2B8"/>'
        '<path d="M264 80C262 50 290 42 304 48C322 52 332 70 328 96C322 72 300 62 280 70C270 74 266 84 264 98Z" fill="#6B3E26"/>'
        '<circle cx="284" cy="86" r="2.6" fill="#2B2B2B"/><circle cx="308" cy="86" r="2.6" fill="#2B2B2B"/>'
        '<path d="M287 100Q296 108 305 100" fill="none" stroke="#B5523C" stroke-width="2.6" stroke-linecap="round"/></svg></div>'
    )


def secure_note(text: str) -> None:
    html('<div class="hc-secure"><svg width="30" height="30" viewBox="0 0 40 40"><path d="M20 3L35 9V20C35 29 28 35 20 38C12 35 5 29 5 20V9Z" fill="#17A34A"/>'
         '<path d="M12 20l6 6 11-12" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
         f'<div>{esc(text)}</div></div>')


def nav(active: str) -> None:
    """Fixed bottom navigation bar."""
    items = [
        ("home", "Home", ":material/home:"),
        ("history", "History", ":material/history:"),
        ("profile", "Profile", ":material/person:"),
        ("logout", "Logout", ":material/logout:"),
    ]
    with st.container(key="bottomnav"):
        cols = st.columns(4)
        for col, (page, label, icon) in zip(cols, items):
            with col:
                st.button(
                    label, icon=icon, key=f"nav_{page}", on_click=go, args=(page,),
                    type="primary" if page == active else "secondary",
                )
