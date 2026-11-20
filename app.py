"""Health Check with Aira: Streamlit app.   Run:  streamlit run app.py"""
import streamlit as st

import services as S
import triage
import ui
import views_care as vc
import views_main as vm

st.set_page_config(page_title="Health Check", page_icon="\U0001FA7A", layout="centered",
                   initial_sidebar_state="collapsed")

# page name -> (function, theme, highlighted bottom-nav item or None for no nav bar)
PAGES = {
    "home": (vm.home, "light", "home"),
    "history": (vm.history, "light", "history"),
    "profile": (vm.profile, "light", "profile"),
    "logout": (vm.logout, "light", None),
    "check": (vc.check, "light", "home"),
    "acne": (vc.acne, "light", "home"),
    "progress": (vc.progress, "light", "history"),
    "aira": (vc.aira, "light", "home"),
    "tips": (vc.tips, "light", "home"),
    "sleep": (vc.sleep, "dark", None),
    "insomnia": (vc.insomnia, "dark", None),
}


def init_state() -> None:
    defaults = {
        "logged_in": False,
        "page": "home",
        "name": "",
        "check_key": "skin",
        "results": {},
        "history": [],
        "risk": dict(triage.DEFAULT_RISK),
        "quick": {},
        "confirm_delete": False,
        "sleep_on": False,
        "sleep_end": 0.0,
        "acne_log": [{"score": s, "sample": True} for s in (62, 58, 55, 47, 44, 38)],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()

if not st.session_state.logged_in:
    ui.inject("login")
    vm.login()
else:
    if st.session_state.page != "sleep":      # leaving Sleep Mode always stops the sound and the timer
        st.session_state.sleep_on = False
    func, theme, active = PAGES.get(st.session_state.page, PAGES["home"])
    ui.inject(theme)
    func()
    if active:
        ui.nav(active)

# Private page for the owner: open the app with ?admin=<ADMIN_KEY> (set ADMIN_KEY in the app secrets) to read feedback.
if S.admin_ok(st.query_params.get("admin", "")):
    import pandas as pd

    with st.expander("Admin: feedback"):
        for name in ("feedback.csv",):
            path = S.DATA_DIR / name
            if path.exists():
                st.write(name)
                st.dataframe(pd.read_csv(path), use_container_width=True)
                st.download_button(f"Download {name}", path.read_bytes(), name, "text/csv", key=f"dl_{name}")
            else:
                st.write(f"No {name} yet.")
