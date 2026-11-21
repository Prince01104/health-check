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
.stButton, [data-testid="stFormSubmitButton"], [data-testid="stFormSubmitButton"] > div, [data-testid="stFormSubmitButton"] button { width: 100% !important; }
[data-testid="stElementContainer"]:has(> .stButton), [data-testid="stElementContainer"]:has([data-testid="stFormSubmitButton"]) { width: 100% !important; }
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
.stApp { background: #F4F5FA !important; }
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"] { color: #1B2A4A; }
.stApp [data-testid="stCaptionContainer"] { color: #5B6478; }
h3 { font-size: 1.15rem !important; margin-top: .6rem !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  background: #FFFFFF; border: 1.5px solid #D5DAE6; color: #0B6665;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { border-color: #0B6665; color: #0B6665; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: #0B6665 !important; border: none !important;
  box-shadow: 0 6px 16px rgba(11,102,101,.25);
}
.stButton > button[kind="primary"] *, button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primaryFormSubmit"] * { color: #FFFFFF !important; }
.hc-card { background: #FFFFFF; border: 1.5px solid #E3E6F0; box-shadow: 0 6px 18px rgba(27,42,74,.06); }
.hc-muted { color: #5B6478; }
.hc-step.on { background: #FFFFFF; border: 2px solid #17A34A; }
.hc-step.off { background: #EAF3EC; border: 1.5px solid #DCEFE1; }
.hc-step.done { background: #FFFFFF; border: 1.5px solid #14603A; }
.hc-num { background: #CFE5D5; color: #25432F; }
.hc-step.on .hc-num { background: #17A34A; color: #FFFFFF; }
.hc-step.done .hc-num { background: #DDF3E6; color: #14603A; }

/* flat bottom navigation, icon above label */
.st-key-bottomnav {
  background: #FFFFFF; border: none; border-top: 1px solid #E3E6F0; border-radius: 0; bottom: 0 !important; box-shadow: none;
  width: min(430px, 100%) !important; padding: 4px 6px 6px 6px;
}
.st-key-bottomnav button { color: #5B6478 !important; border: none !important; border-radius: 14px !important; background: transparent !important;
  min-height: 54px !important; box-shadow: none !important; padding: 4px 0 !important; }
.st-key-bottomnav button span[data-has-shortcut] { flex-direction: column !important; gap: 2px !important; align-items: center !important; justify-content: center; }
.st-key-bottomnav button p { font-size: 12px !important; font-weight: 700 !important; margin: 0 !important; line-height: 1.2 !important; }
.st-key-bottomnav .stButton > button, .st-key-bottomnav .stButton > button[kind="primary"], .st-key-bottomnav button[data-testid="stBaseButton-primary"] {
  background: transparent !important; box-shadow: none !important; border: none !important; }
.st-key-bottomnav button[kind="primary"], .st-key-bottomnav button[data-testid="stBaseButton-primary"] { color: #0B6665 !important; }
.st-key-bottomnav button[kind="primary"] *, .st-key-bottomnav button[data-testid="stBaseButton-primary"] * { color: #0B6665 !important; }

/* home (quick checks) */
[class*="st-key-hm_"] { position: relative; box-sizing: border-box; overflow: hidden; border-radius: 28px; margin: 0 0 10px 0; }
[class*="st-key-hm_"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
[class*="st-key-hm_"] [data-testid="stMarkdownContainer"], [class*="st-key-hm_"] [data-testid="stMarkdown"] { margin-bottom: 0 !important; }
.hm-in { display: flex; flex-direction: column; padding: 16px; box-sizing: border-box; }
.hm-ic { width: 46px; height: 46px; border-radius: 14px; background: #FFFFFF; display: flex; align-items: center; justify-content: center; flex: none; }
.hm-circ { width: 34px; height: 34px; border-radius: 50%; background: rgba(255,255,255,.8); display: flex; align-items: center; justify-content: center; flex: none; }
.hm-t { font-size: 20px; font-weight: 800; letter-spacing: -0.01em; color: #1B2A4A; line-height: 1.2; }
.hm-s { font-size: 14px; color: #4A5470; line-height: 1.35; margin-top: 3px; }
.hm-h { font-size: 22px; font-weight: 800; letter-spacing: -0.02em; color: #1B2A4A; margin: 18px 0 10px 0; }
.hm-tag { display: inline-block; background: rgba(255,255,255,.75); border-radius: 999px; padding: 5px 12px; font-size: 12px; font-weight: 800; letter-spacing: .03em; color: #1B2A4A; }
.hm-pill { display: inline-block; background: #FFFFFF; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 800; color: #1B2A4A; margin-top: 4px; }
.hm-soon { display: flex; align-items: center; gap: 10px; border: 1.5px dashed #B9C0D6; border-radius: 20px; padding: 12px; background: #ECEFF8; margin: 0 0 12px 0; box-sizing: border-box; }
.hm-soon .hm-ic { width: 40px; height: 40px; }
.st-key-hm_news { background: #E4E1F8; } .st-key-hm_skin { background: #FADDCF; } .st-key-hm_oral { background: #D9EFE0; }
.st-key-hm_acne { background: #FAE5B5; }
.st-key-hm_sleep, .st-key-hm_insomnia, .st-key-hm_aira { background: #FFFFFF; border: 1px solid #E3E6F0; border-radius: 22px; }
.st-key-newshead { position: relative; }
.st-key-newshead [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-seeall { position: absolute !important; right: 0 !important; left: auto !important; top: 0; bottom: 0; width: auto !important; z-index: 2;
  display: flex !important; align-items: center; justify-content: flex-end; }
.st-key-seeall > div, .st-key-seeall [data-testid="stElementContainer"], .st-key-seeall .stButton { width: auto !important; }
.st-key-seeall button { background: transparent !important; border: none !important; box-shadow: none !important; min-height: 0 !important; padding: 4px 0 !important; width: auto !important; }
.st-key-seeall button p { color: #1B2A4A !important; font-weight: 800 !important; font-size: 15px !important; }
/* bento home (old) */
.hc-greet-a { font-size: 32px; font-weight: 400; color: #5B6478; line-height: 1.1; letter-spacing: -0.02em; }
.hc-greet-b { font-size: 38px; font-weight: 800; color: #1B2A4A; line-height: 1.15; letter-spacing: -0.02em; }
.hc-foot { text-align: center; font-size: 13px; color: #5B6478; margin: 14px 0 70px 0; }
[class*="st-key-bt_"] { position: relative; border-radius: 28px; padding: 16px; box-sizing: border-box; overflow: hidden; }
[class*="st-key-bt_"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
[class*="st-key-bt_"] [data-testid="stMarkdownContainer"], [class*="st-key-bt_"] [data-testid="stMarkdown"] { margin-bottom: 0 !important; }
[class*="st-key-tile_"] { position: absolute !important; inset: 0; z-index: 3; width: 100% !important; }
[class*="st-key-tile_"] button { width: 100% !important; height: 100% !important; opacity: 0; border-radius: 28px !important; }
.st-key-bt_aira { background: #E4E1F8; } .st-key-bt_skin { background: #FADDCF; } .st-key-bt_oral { background: #DCE8B2; }
.st-key-bt_acne { background: #FAE5B5; } .st-key-bt_sleep { background: #D5E4F5; }
.st-key-bt_insomnia { background: #DCEDE5; } .st-key-bt_tips { background: #F8DCE8; }
.bt-in { display: flex; flex-direction: column; justify-content: space-between; }
.bt-ic { width: 44px; height: 44px; border-radius: 14px; background: #FFFFFF; display: flex; align-items: center; justify-content: center; flex: none; }
.bt-t { font-size: 18px; font-weight: 800; color: #1B2A4A; line-height: 1.2; }
.bt-s { font-size: 13px; color: #46506A; line-height: 1.3; }
.bt-art { align-self: flex-start; position: relative; width: 100px; height: 100px; margin: 0 0 0 10px; }
.bt-art span:first-child { position: absolute; left: 0; top: 36px; width: 100px; height: 28px; border-radius: 14px; }
.bt-art span:last-child { position: absolute; left: 36px; top: 0; width: 28px; height: 100px; border-radius: 14px; }


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
[data-testid="stFileUploaderDropzone"] button { background: #0B6665 !important; border: none !important;
  border-radius: 999px !important; min-height: 44px !important; padding: 0 22px !important; }
[data-testid="stFileUploaderDropzone"] button * { color: #FFFFFF !important; font-weight: 800 !important; }
.hc-secure { display: flex; gap: 12px; align-items: center; background: #DDF5E3; border-radius: 18px; padding: 12px 14px;
  font-size: 13px; line-height: 1.4; margin: 0 0 12px 0; }
[data-testid="stExpander"] { border: 1.5px solid #DCEFE1 !important; border-radius: 18px !important; background: #FFFFFF; }
[data-testid="stProgress"] > div > div > div > div { background-color: #17A34A !important; }

/* ---- new check / acne design ---- */
.st-key-hdr { position: relative; min-height: 54px; margin: 0 0 4px 0; }
.st-key-hdr [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-hdr .stButton { position: absolute; left: 0; top: 2px; width: auto !important; z-index: 2; }
.st-key-hdr .stButton > button { width: 44px !important; min-height: 44px !important; height: 44px; padding: 0 !important;
  border-radius: 14px !important; background: #FFFFFF !important; border: 1px solid #E3E6F0 !important; box-shadow: 0 2px 8px rgba(27,42,74,.06) !important; }
.st-key-hdr .stButton > button p { display: none; }
.st-key-hdr .stButton > button [data-testid="stIconMaterial"] { color: #1B2A4A; }
.hdr-t { padding-left: 58px; }
.hdr-t .a { font-size: 25px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; color: #1B2A4A; }
.hdr-t .b { font-size: 13px; color: #5B6478; line-height: 1.3; margin-top: 2px; }
.hc-h { font-size: 17px; font-weight: 800; margin: 14px 0 8px 0; color: #1B2A4A; }
.hc-h small { font-size: 13px; font-weight: 500; color: #5B6478; margin-left: 4px; }
[class*="st-key-src_"], [class*="st-key-src_"] > div, [class*="st-key-src_"] .stButton, [class*="st-key-src_"] [data-testid="stElementContainer"] { width: 100% !important; }
[class*="st-key-src_"] .stButton > button { height: 96px; min-height: 96px !important; border-radius: 22px !important; border: none !important;
  box-shadow: none !important; padding: 12px 14px !important; justify-content: flex-start !important; align-items: stretch !important; color: #1B2A4A !important; }
[class*="st-key-src_"] .stButton > button span[data-has-shortcut], [class*="st-key-src_"] .stButton > button > div {
  flex-direction: column !important; align-items: flex-start !important; justify-content: space-between !important; gap: 0 !important; height: 100%; width: 100%; }
[class*="st-key-src_"] .stButton > button [data-testid="stIconMaterial"] { background: #FFFFFF; border-radius: 12px; width: 40px !important; height: 40px !important;
  min-width: 40px !important; box-sizing: border-box; flex: none; display: flex; align-items: center; justify-content: center; font-size: 22px !important; color: #1B2A4A !important; }
[class*="st-key-src_"] .stButton > button p { font-size: 16px !important; font-weight: 800 !important; color: #1B2A4A !important; }
.st-key-src_skin_up button, .st-key-src_acne_up button { background: #FADDCF !important; }
.st-key-src_skin_cam button, .st-key-src_acne_cam button { background: #D5EBDD !important; }
.st-key-src_oral_up button { background: #DCE8B2 !important; }
.st-key-src_oral_cam button { background: #D5E4F5 !important; }
[class*="st-key-drop_"] [data-testid="stFileUploaderDropzone"] { border: 2px dashed rgba(27,42,74,.25) !important; min-height: 130px; justify-content: center; }
.st-key-drop_skin [data-testid="stFileUploaderDropzone"], .st-key-drop_acne [data-testid="stFileUploaderDropzone"] { background: #FADDCF !important; }
.st-key-drop_oral [data-testid="stFileUploaderDropzone"] { background: #DCE8B2 !important; }
.hc-hint { text-align: center; font-size: 13px; color: #5B6478; margin: -2px 0 10px 0; }
.hc-drop { border-radius: 22px; min-height: 130px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 14px; text-align: center; font-size: 14px; color: #1B2A4A; margin: 0 0 10px 0; }
.hc-drop.skin, .hc-drop.acne { background: #FADDCF; } .hc-drop.oral { background: #DCE8B2; }
[class*="st-key-prev_"] { border-radius: 22px; padding: 10px; margin: 0 0 10px 0; }
.st-key-prev_skin, .st-key-prev_acne { background: #FADDCF; } .st-key-prev_oral { background: #DCE8B2; }
.hc-ok { display: flex; align-items: center; gap: 8px; background: #DDF3E6; color: #14603A; border-radius: 12px; padding: 9px 12px;
  font-size: 13px; font-weight: 700; margin: 0 0 6px 0; }
.hc-ok.warn { background: #FDF1D6; color: #7A5200; }
.st-key-quick { background: #FFFFFF; border: 1px solid #E3E6F0; border-radius: 20px; padding: 14px 14px 6px 14px; margin: 0 0 12px 0; }
.st-key-quick p { margin: 0 0 6px 0; }
.hc-q { font-size: 14px; font-weight: 700; color: #1B2A4A; margin: 4px 0 6px 0; }
button[data-variant="pills"] { border-radius: 999px !important; min-height: 34px !important; font-size: 13px !important; font-weight: 600 !important;
  background: #F4F5FA !important; border: 1px solid #D5DAE6 !important; color: #1B2A4A !important; box-shadow: none !important; }
button[data-variant="pills"] * { color: #1B2A4A !important; }
button[data-variant="pills"][data-selected="true"], button[data-variant="pills"][aria-checked="true"] { background: #0B6665 !important; border-color: #0B6665 !important; }
button[data-variant="pills"][data-selected="true"] *, button[data-variant="pills"][aria-checked="true"] * { color: #FFFFFF !important; }
[data-testid="stCheckbox"] label p { font-size: 13px; }
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child { border-color: #5B6478 !important; border-radius: 6px !important; }
[data-testid="stCheckbox"] input:checked + div { background: #0B6665 !important; border-color: #0B6665 !important; }
.rc { border-radius: 20px; padding: 16px; margin: 0 0 12px 0; border: 1.5px solid transparent; }
.rc .k { font-size: 11px; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; }
.rc .big { font-size: 28px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; margin: 4px 0 8px 0; }
.rc .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.rc .chip { background: #FFFFFF; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 800; }
.rc .txt { font-size: 14px; line-height: 1.5; color: #1B2A4A; }
.rc.doctor { background: #FBE3E0; border-color: #F0B9B3; } .rc.doctor .k { color: #B3261E; }
.rc.watch { background: #FDF1D6; border-color: #F0D9A0; } .rc.watch .k { color: #8A6A10; }
.rc.routine { background: #DDF3E6; border-color: #B9E2C9; } .rc.routine .k { color: #14603A; }
.rc.retake { background: #FCE9DA; border-color: #F0C9A8; } .rc.retake .k { color: #B4531A; }
.wc { background: #FFFFFF; border: 1.5px solid #E3E6F0; border-radius: 20px; padding: 14px 16px; margin: 0 0 12px 0; }
.wc .k { font-size: 11px; font-weight: 800; letter-spacing: .04em; color: #5B6478; text-transform: uppercase; margin-bottom: 6px; }
.wc ul { margin: 0; padding-left: 18px; } .wc li { font-size: 14px; line-height: 1.5; margin: 2px 0; }
.duo { display: flex; gap: 10px; margin: 0 0 12px 0; }
.duo > div { flex: 1; border-radius: 18px; padding: 12px 14px; min-width: 0; }
.duo .k { font-size: 11px; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 6px; }
.duo ul { margin: 0; padding-left: 16px; } .duo li { font-size: 13px; line-height: 1.45; margin: 2px 0; }
.duo .g { background: #DDF3E6; } .duo .g .k { color: #14603A; } .duo .r { background: #FBE3E0; } .duo .r .k { color: #B3261E; }
.st-key-heatcard { background: #FFFFFF; border: 1.5px solid #E3E6F0; border-radius: 20px; padding: 12px; margin: 0 0 12px 0; }
.legend { height: 8px; border-radius: 6px; background: linear-gradient(90deg, #3B6FD8, #35B9C9, #7BD16B, #F2D13B, #F2833B, #E0452F); margin: 4px 0 6px 0; }
.legend-l { display: flex; justify-content: space-between; font-size: 12px; color: #5B6478; }
.bar-row { margin: 10px 0 2px 0; } .bar-row .t { display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.bar { height: 8px; border-radius: 5px; background: #E6EAF2; overflow: hidden; } .bar > i { display: block; height: 100%; background: #0B6665; border-radius: 5px; }
.stat2 { display: flex; gap: 10px; margin-top: 10px; }
.stat2 > div { flex: 1; background: rgba(255,255,255,.65); border-radius: 14px; padding: 10px 12px; }
.stat2 .l { font-size: 12px; color: #5B6478; } .stat2 .v { font-size: 20px; font-weight: 800; }
.ba { display: flex; gap: 10px; } .ba > div { flex: 1; min-width: 0; text-align: left; }
.ba .ph { border-radius: 14px; aspect-ratio: 1 / .62; display: flex; align-items: center; justify-content: center; font-size: 13px; color: #1B2A4A; overflow: hidden; }
.ba .ph img { width: 100%; height: 100%; object-fit: cover; }
.ba .cap { display: flex; justify-content: space-between; font-size: 13px; margin-top: 6px; } .ba .cap b { font-weight: 800; } .ba .cap span { color: #5B6478; }
.aira-say { background: #DDF3E6; color: #14603A; border-radius: 12px; padding: 10px 12px; font-size: 14px; margin-top: 10px; }
.trend { display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; height: 150px; padding: 4px 4px 0 4px; }
.trend > div { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; }
.trend i { display: block; width: 100%; max-width: 30px; border-radius: 8px; background: #EBC3D2; }
.trend i.now { background: #B4426F; }
.trend span { font-size: 11px; color: #5B6478; margin-top: 6px; white-space: nowrap; } .trend span.now { color: #1B2A4A; font-weight: 800; }
.ci { display: flex; align-items: center; gap: 12px; background: #FFFFFF; border: 1.5px solid #E3E6F0; border-radius: 18px; padding: 10px 12px; margin: 0 0 10px 0; }
.ci .ic { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex: none; font-size: 18px; }
.ci .m { flex: 1; min-width: 0; } .ci .m b { display: block; font-size: 15px; } .ci .m span { font-size: 13px; color: #5B6478; }
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
.stApp { background-color: #F4F5FA !important;
  background-image: radial-gradient(circle at 8% 6%, rgba(196,188,246,.55), transparent 36%),
                    radial-gradient(circle at 100% 36%, rgba(250,205,180,.55), transparent 34%),
                    radial-gradient(circle at 14% 98%, rgba(190,235,205,.65), transparent 40%) !important; }
.stApp, .stApp p, .stApp label, .stApp h1, .stApp span, .stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] p { color: #1B2A4A; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: #5B6478; text-align: center; }
[data-testid="stWidgetLabel"] p { font-size: 16px; font-weight: 700; }
[data-testid="stTextInputRootElement"], [data-testid="stTextInputRootElement"] > div, [data-baseweb="base-input"], [data-baseweb="input"] {
  background: #FFFFFF !important; border-radius: 999px !important; }
[data-testid="stTextInputRootElement"] { border: 1.5px solid #D9DEEA !important; min-height: 50px; box-shadow: none !important; }
[data-testid="stTextInputRootElement"] input { color: #1B2A4A !important; -webkit-text-fill-color: #1B2A4A !important; padding-left: 20px !important; font-size: 16px; }
[data-testid="stTextInputRootElement"] input::placeholder { color: #8A93A8 !important; -webkit-text-fill-color: #8A93A8 !important; opacity: 1; }
[data-testid="stTextInputRootElement"]:focus-within { border-color: #0B6665 !important; }
[data-testid="stCheckbox"] label p { color: #5B6478 !important; font-size: 13px; font-weight: 500 !important; }
[data-testid="stFormSubmitButton"], [data-testid="stFormSubmitButton"] > div, [data-testid="stFormSubmitButton"] button { width: 100% !important; }
[data-testid="stFormSubmitButton"] > button { background: #0B6665 !important; border: none !important; border-radius: 18px !important; min-height: 54px;
  box-shadow: 0 8px 20px rgba(11,102,101,.25); }
[data-testid="stFormSubmitButton"] > button * { color: #FFFFFF !important; font-weight: 800; font-size: 17px; }
[data-testid="stAlert"] { border-radius: 16px; }
.lg-chips { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin: 6px 0 22px 0; }
.lg-chips span { border-radius: 999px; padding: 9px 16px; font-size: 15px; font-weight: 800; }
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


def header(title: str, subtitle: str = "", target: str = "home") -> None:
    """Page header: round back button on the left, title and a small subtitle."""
    with st.container(key="hdr"):
        st.button("Back", icon=":material/arrow_back:", key=f"back_{target}_Back", on_click=go, args=(target,))
        html(f'<div class="hdr-t"><div class="a">{esc(title)}</div><div class="b">{esc(subtitle)}</div></div>')


def aira(size: int = 150, sleepy: bool = False, suffix: str = "a") -> str:
    """Profosa, the original humanoid guide, as inline SVG."""
    eyes = (
        '<path d="M45 56q5 4 10 0M65 56q5 4 10 0" fill="none" stroke="#7CF2E0" stroke-width="2.4" stroke-linecap="round"/>'
        if sleepy
        else '<ellipse class="aira-eye" cx="50" cy="56" rx="4" ry="5" fill="#7CF2E0"/>'
             '<ellipse class="aira-eye" cx="70" cy="56" rx="4" ry="5" fill="#7CF2E0"/>'
    )
    h = round(size * 140 / 120)
    return (
        f'<svg width="{size}" height="{h}" viewBox="0 0 120 140" role="img" aria-label="Profosa, your AI health companion">'
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
