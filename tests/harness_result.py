"""Tiny page used only by the tests: shows the result view for a result that is put in session state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st  # noqa: E402

import ui  # noqa: E402
import views_care as vc  # noqa: E402

ui.inject("light")
st.session_state.setdefault("results", {"skin": st.session_state["_test_result"]})
st.session_state.setdefault("history", [])
_r = st.session_state.results["skin"]
if "next" not in _r:                         # what S.record() adds in the real app
    import services as S
    S.st.session_state.setdefault("history", [])
    S.record(_r)
vc._show_result("skin", st.session_state.results["skin"])
