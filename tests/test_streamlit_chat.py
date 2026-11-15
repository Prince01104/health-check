"""Streamlit chat box test with a fake Gemini (no key, no internet). Uses the random demo models from test_api."""
import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tests.test_api import client  # noqa: F401  (importing it creates the temp demo models)

APP = str(Path(__file__).resolve().parent.parent / "streamlit_app" / "streamlit_app.py")
pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from backend import chat, ml  # noqa: E402


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("HC_DATA_DIR", str(tmp_path))
    seen = []

    def fake(key, system, turns):
        seen.append(turns)
        if "fail" in turns[-1]["text"]:
            raise RuntimeError("down")
        return "It may be this. Keep the skin clean.\nThis is AI screening, not a diagnosis."
    monkeypatch.setattr(chat, "_generate", fake)

    ml.warm_up()
    img = Image.fromarray((np.random.rand(300, 300, 3) * 255).astype("uint8"))
    r = ml.predict("skin", img)
    cam = r.pop("cam")
    base, heat = ml.overlay(img, cam)
    r.update(rid="t1", check="skin", quality=ml.quality_check(img), base=base, heat=heat, demo=True)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["view"], at.session_state["check"], at.session_state["result"] = "result", "skin", r
    at.seen = seen
    return at.run()


def texts(at):
    return [m.markdown[0].value if m.markdown else "" for m in at.chat_message]


def test_chat_box_is_shown_below_result(app):
    assert not app.exception
    assert any("Ask about this result" in x.value for x in app.markdown)
    assert len(app.chat_input) == 1


def test_quick_question_and_follow_up_keep_history(app):
    app.button(key="chatq_0").click().run()
    assert not app.exception and len(app.chat_message) == 2
    assert "AI screening" in texts(app)[1]
    app.chat_input[0].set_value("And care tips?").run()
    assert len(app.chat_message) == 4
    assert [m["text"] for m in app.seen[-1]][:2] == ["What can this be?", app.session_state["chat"][1]["text"]]
    assert app.seen[-1][-1]["text"] == "And care tips?"


def test_failure_is_friendly_and_result_stays(app):
    app.chat_input[0].set_value("please fail").run()
    assert not app.exception
    assert any("not available right now" in w.value for w in app.warning)
    assert any("Possible" in m.value for m in app.markdown)           # CNN result still there


def test_new_photo_resets_chat_and_hindi_works(app):
    app.chat_input[0].set_value("hello").run()
    assert len(app.chat_message) == 2
    app.radio(key="lang_pick").set_value("हिन्दी").run()
    assert not app.exception and any("इस नतीजे के बारे में पूछें" in x.value for x in app.markdown)
    r = dict(app.session_state["result"]); r["rid"] = "other"
    app.session_state["result"] = r
    app.run()
    assert len(app.chat_message) == 0


def test_question_limit(app):
    for i in range(16):
        app.chat_input[0].set_value(f"q{i}").run()
    assert len(app.seen) == 15
    assert any("limit" in w.value for w in app.warning)
