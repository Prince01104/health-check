"""AppTest checks for every page, with a fake Gemini (no key, no internet).  Run from this folder:  python -m pytest -q"""
import io
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

import chat  # noqa: E402
import ml  # noqa: E402
import services as S  # noqa: E402

APP = str(ROOT / "app.py")


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("HC_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(S, "DATA_DIR", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    seen = []

    def fake(key, system, turns):
        seen.append((system, turns))
        if "fail" in turns[-1]["text"]:
            raise RuntimeError("down")
        return "It may be this. Keep the skin clean.\nThis is AI screening, not a diagnosis."
    monkeypatch.setattr(chat, "_generate", fake)
    return seen


def photo():
    arr = (np.random.rand(300, 300, 3) * 255).astype("uint8")
    b = io.BytesIO()
    Image.fromarray(arr).save(b, "JPEG")
    return b.getvalue()


def app(page="home", **state):
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["logged_in"], at.session_state["page"] = True, page
    for k, v in state.items():
        at.session_state[k] = v
    return at.run()


def texts(at):
    return " ".join(m.value for m in at.markdown)


def test_login_demo_mode_consent_and_name_from_email():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert [t.label for t in at.text_input] == ["Email", "Password"] and at.text_input[1].proto.type == 1
    at.text_input[0].set_value("prince.s@example.com")
    at.text_input[1].set_value("whatever")
    at.button[0].click().run()
    assert not at.session_state["logged_in"] and "tick the box" in " ".join(e.value for e in at.error)   # consent first
    at.text_input[0].set_value("prince.s@example.com")
    at.checkbox[0].check()
    at.button[0].click().run()
    assert at.session_state["logged_in"] and at.session_state["page"] == "home"
    assert at.session_state["name"] == "Prince"                       # only the first name is kept, never the email or password
    kept = str({k: at.session_state[k] for k in ("name", "history", "results", "risk")})
    assert "example.com" not in kept and "whatever" not in kept


def test_login_with_blank_fields_still_works_and_html_in_email_is_stripped():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input[0].set_value("<b>x</b>")
    at.checkbox[0].check()
    at.button[0].click().run()
    assert at.session_state["logged_in"] and "<" not in at.session_state["name"] and at.session_state["name"].isalpha()   # letters only, no markup


@pytest.mark.parametrize("page", ["home", "history", "profile", "logout", "check", "acne", "aira", "tips", "progress", "sleep", "insomnia"])
def test_every_page_renders(page):
    at = app(page)
    assert not at.exception, at.exception


def test_home_marks_untrained_checks_coming_soon():
    at = app("home")
    for key in ("aira", "skin", "oral", "acne", "sleep", "insomnia", "tips"):
        assert not at.button(key=f"tile_{key}").disabled, key
    assert not [b for b in at.button if "Feeling lonely" in b.label]        # the lonely feature is gone


def test_unready_check_says_coming_soon():
    at = app("check", check_key="nail")
    assert not at.exception and "Coming soon" in texts(at)


def test_profile_escapes_name():
    at = app("profile", name="<script>alert(1)</script>")
    assert "<script>" not in texts(at) and "&lt;script&gt;" in texts(at)


def test_real_models_load_and_predict():
    for key in ("oral", "skin"):
        assert S.model_ready(key) and not S.is_demo(key)
        res = S.analyse(key, io.BytesIO(photo()))
        assert res["status"] in ("ok", "uncertain", "invalid") and 0 <= res["confidence"] <= 1
        assert len(res["probs"]) == len(ml.classes_of(key))
        assert res["base"] is not None


def test_exif_rotation_is_applied():
    img = Image.fromarray((np.random.rand(200, 300, 3) * 255).astype("uint8"))
    exif = Image.Exif(); exif[0x0112] = 6                         # camera says: rotate 90 degrees
    b = io.BytesIO(); img.save(b, "JPEG", exif=exif)
    res = S.analyse("skin", io.BytesIO(b.getvalue()))
    assert res["base"].shape[0] > res["base"].shape[1]            # now portrait (was landscape)


def result_app(status="ok"):
    res = S.analyse("skin", io.BytesIO(photo()))
    res["photo"] = "x"
    if status != "keep":
        res["status"] = status
    at = AppTest.from_file(str(ROOT / "tests" / "harness_result.py"), default_timeout=120)
    at.session_state["_test_result"] = res
    return at.run(), res


def test_chat_flow_with_history_errors_and_limit(env):
    at, res = result_app("ok")
    assert not at.exception and any("Ask Aira" in m.value for m in at.markdown)
    at.button(key="explain_skin").click().run()
    assert not at.exception and [r for r, _ in at.session_state["results"]["skin"]["chat"]] == ["user", "aira"]
    assert len(at.chat_message) == 2 and "not a diagnosis" in at.chat_message[1].markdown[0].value
    system, turns = env[-1]
    assert "Aira" in system and "not a doctor" in system and "MODEL RESULT" in system and turns[-1]["role"] == "user"
    at.text_input[0].set_value("And care tips?")
    [b for b in at.button if b.label == "Send"][0].click().run()
    chat_now = at.session_state["results"]["skin"]["chat"]
    assert [t for r, t in chat_now if r == "user"][-1] == "And care tips?"
    assert [t["text"] for t in env[-1][1]][0] == "Explain this result in simple words and what I should do next."   # history kept
    at.text_input[0].set_value("please fail")
    [b for b in at.button if b.label == "Send"][0].click().run()
    assert at.session_state["results"]["skin"]["chat"][-1][0] == "err" and any("still valid" in w.value for w in at.warning)
    assert any("SCREENING RESULT" in m.value.upper() for m in at.markdown)        # CNN result still there


def test_question_limit():
    at, res = result_app("ok")
    res_state = at.session_state["results"]["skin"]
    res_state["chat"] = [("user", f"q{i}") if i % 2 == 0 else ("aira", "a") for i in range(2 * S.MAX_QUESTIONS)]
    at.run()
    at.text_input[0].set_value("one more")
    [b for b in at.button if b.label == "Send"][0].click().run()
    assert at.session_state["results"]["skin"]["chat"][-1][0] == "err"
    assert "limit" in at.session_state["results"]["skin"]["chat"][-1][1]


def test_invalid_photo_has_no_chat_and_uncertain_says_not_sure():
    at, _ = result_app("invalid")
    assert not at.exception and not any("Ask Aira" in m.value for m in at.markdown)
    at, _ = result_app("uncertain")
    assert any("Not sure" in m.value for m in at.markdown) and any("Ask Aira" in m.value for m in at.markdown)


def test_feedback_saved_without_photo_or_name():
    at, res = result_app("ok")
    fb = [t for t in at.text_input if "improve" in t.label][0]
    fb.set_value("nice work")
    [b for b in at.button if b.label == "Send feedback"][0].click().run()
    rows = (S.DATA_DIR / "feedback.csv").read_text().splitlines()
    assert len(rows) == 2 and "nice work" in rows[1] and "jpg" not in rows[1] and any("Thank you" in s.value for s in at.success)


def test_acne_sample_data_is_not_presented_as_a_real_trend():
    at = app("acne", acne_log=[{"score": s, "sample": True} for s in (62, 58, 55, 47, 44, 38)])
    t = texts(at)
    assert "Improving" not in t and "No check-in yet" in t
    at.button(key="clear_sample").click().run()
    assert not at.exception and not at.session_state["acne_log"]


def test_acne_real_trend_still_works():
    at = app("acne", acne_log=[{"score": s, "sample": False} for s in (60, 50, 40, 30)])
    assert "Improving" in texts(at)


def test_leaving_sleep_mode_stops_it():
    at = app("sleep", sleep_on=True, sleep_end=1e12)
    at.session_state["page"] = "home"
    at.run()
    assert at.session_state["sleep_on"] is False


def test_insomnia_scores():
    at = app("insomnia")
    for i in range(5):
        at.radio(key=f"ins_{i}").set_value("Yes")
    at.run()
    assert "Possible insomnia" in texts(at)


