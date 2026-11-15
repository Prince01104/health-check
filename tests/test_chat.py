"""Chat tests. Gemini is replaced by a fake, so no API key or internet is needed.  Run:  python -m pytest -q"""
import json

import pytest

from backend import chat
from tests.test_api import client, photo, signup  # noqa: F401  (reuse the temp models and fixtures)

PROBS = [{"label": "psoriasis", "p": 0.78}, {"label": "eczema", "p": 0.15}, {"label": "tinea", "p": 0.05},
         {"label": "unknown_normal", "p": 0.02}]


class FakeGemini:
    """Replaces chat._generate and remembers what would have been sent."""
    def __init__(self, reply="It may be psoriasis. Keep the skin moisturised.\nThis is AI screening, not a diagnosis."):
        self.reply, self.calls = reply, []

    def __call__(self, key, system, turns):
        self.calls.append({"key": key, "system": system, "turns": turns})
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.fixture
def fake(monkeypatch):
    f = FakeGemini()
    monkeypatch.setattr(chat, "_generate", f)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")      # fake key, used only to pass the "is a key set" check
    return f


def ask(**kw):
    args = dict(check="skin", label="psoriasis", confidence=0.78, status="ok", probs=PROBS, history=[],
                message="What is this?", doctor="dermatologist", api_key="test-key")
    args.update(kw)
    return chat.ask(**args)


# ------------------------------------------------------------------ prompt
def test_prompt_has_result_and_all_safety_rules(fake):
    r = ask()
    assert r["ok"]
    system = fake.calls[0]["system"]
    assert "Psoriasis 78%, Eczema 15%, Tinea 5%" in system          # top 3 only, with confidence
    assert "Unknown Normal" not in system and "Normal" not in system.split("Top predictions:")[1].split("\n")[0]
    for rule in ("not a doctor", "final diagnosis", "below 60%", "prescription medicines", "SkinCancer",
                 "fever, fast-spreading redness, pus or severe pain", "Hindi, Hinglish or English",
                 "AI screening, not a diagnosis"):
        assert rule in system
    assert "see a dermatologist soon" in system


def test_only_text_is_sent(fake):
    ask(message="my knee hurts")
    sent = json.dumps(fake.calls[0])
    assert "my knee hurts" in sent
    for forbidden in ("@", "Prince", "history_id", "jpg", "base64"):
        assert forbidden not in sent


def test_history_is_kept_and_trimmed(fake):
    hist = [{"role": "assistant", "text": "stray first turn"}]
    for i in range(30):
        hist += [{"role": "user", "text": f"q{i}"}, {"role": "assistant", "text": f"a{i}"}]
    ask(history=hist, message="last question")
    turns = fake.calls[0]["turns"]
    assert len(turns) <= chat.MAX_HISTORY + 1
    assert turns[0]["role"] == "user" and turns[-1] == {"role": "user", "text": "last question"}
    assert all(t["role"] in ("user", "model") for t in turns)


def test_long_message_is_cut_and_empty_is_rejected(fake):
    ask(message="x" * 5000)
    assert len(fake.calls[0]["turns"][-1]["text"]) == chat.MAX_MESSAGE
    assert ask(message="   ")["error"] == "empty"
    assert len(fake.calls) == 1


# ------------------------------------------------------------------ safety
def test_low_confidence_must_say_not_sure(fake):
    fake.reply = "It could be eczema. Moisturise daily."
    r = ask(confidence=0.41, status="uncertain", label="eczema")
    assert r["flags"]["low_conf"]
    assert "not sure" in r["reply"].lower() and "doctor" in r["reply"].lower()
    assert r["reply"].splitlines()[-1] == "This is AI screening, not a diagnosis."
    assert "below 60%" in fake.calls[0]["system"] and "Confidence below 60% or unsure: yes" in fake.calls[0]["system"]


@pytest.mark.parametrize("text", ["I have fever since 2 days", "there is pus in it", "very severe pain",
                                  "redness is spreading fast", "mujhe bukhar hai", "bahut dard hai",
                                  "तेज बुखार है", "मवाद निकल रहा है", "लालिमा तेजी से फैल रही है"])
def test_red_flags_force_doctor_advice(fake, text):
    fake.reply = "Keep the area clean and dry."
    r = ask(message=text)
    assert r["flags"]["red_flag"], text
    low = r["reply"].lower()
    assert ("dermatologist" in low and "soon" in low) or "जल्द" in r["reply"], r["reply"]


def test_red_flag_in_earlier_turn_still_counts(fake):
    fake.reply = "Rest and drink water."
    r = ask(history=[{"role": "user", "text": "I have fever"}, {"role": "model", "text": "ok"}], message="what to eat?")
    assert r["flags"]["red_flag"] and "dermatologist" in r["reply"]


def test_cancer_label_forces_doctor_advice(fake):
    fake.reply = "This needs attention."
    r = ask(label="SkinCancer", confidence=0.9, probs=[{"label": "SkinCancer", "p": 0.9}])
    assert r["flags"]["urgent_label"] and "dermatologist" in r["reply"] and "soon" in r["reply"]


def test_normal_answer_is_not_polluted(fake):
    r = ask()
    assert not any(r["flags"].values())
    assert "see a dermatologist" not in r["reply"] and "not sure" not in r["reply"].lower()


def test_disclaimer_added_when_missing_and_kept_last(fake):
    fake.reply = "**Moisturise** daily.\n* avoid soap"
    r = ask()
    assert r["reply"].endswith("This is AI screening, not a diagnosis.")
    assert "**" not in r["reply"] and "• avoid soap" in r["reply"]


def test_hindi_reply_gets_hindi_lines(fake):
    fake.reply = "यह सोरायसिस हो सकता है। त्वचा को नम रखें।"
    r = ask(message="bukhar hai", doctor="dermatologist")
    assert "त्वचा रोग विशेषज्ञ" in r["reply"] and r["reply"].endswith("निदान नहीं।")


def test_oral_check_uses_dentist(fake):
    fake.reply = "Brush gently."
    r = ask(check="oral", label="gingivitis", message="there is pus", doctor="dentist")
    assert "dentist" in r["reply"] and "see a dentist soon" in fake.calls[0]["system"]


# ------------------------------------------------------------------- errors
def test_no_key_is_friendly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert ask(api_key=None)["error"] == "not_configured"


class Quota(Exception):
    code = 429


class ReadTimeout(Exception):
    pass


@pytest.mark.parametrize("exc,kind", [(Quota("quota"), "busy"), (ReadTimeout("slow"), "timeout"),
                                      (TimeoutError("slow"), "timeout"), (RuntimeError("boom"), "unavailable")])
def test_gemini_errors_never_raise(fake, exc, kind):
    fake.reply = exc
    r = ask()
    assert r["ok"] is False and r["error"] == kind and r["reply"] is None


def test_empty_gemini_answer_is_an_error(fake):
    fake.reply = ""
    assert ask()["error"] == "unavailable"


def test_api_key_never_printed(fake, capsys):
    fake.reply = RuntimeError("boom")
    ask(api_key="SECRET-KEY-123")
    out = capsys.readouterr()
    assert "SECRET-KEY-123" not in out.out + out.err


# ----------------------------------------------------------------- endpoint
def test_chat_endpoint(client, fake):
    h = signup(client, "chat1@x.com")
    res = client.post("/api/predict/skin", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()
    hid = res["id"]
    r = client.post("/api/chat", headers=h, json={"history_id": hid, "message": "What can this be?"})
    assert r.status_code == 200 and r.json()["ok"] and r.json()["reply"].endswith("not a diagnosis.")
    sent = fake.calls[-1]
    assert "check type: skin" in sent["system"].lower() or "Check type: skin" in sent["system"]
    # the server uses the stored result, so the browser cannot fake a different one
    top = res["probs"][0]["label"].replace("_", " ").title()
    assert top in sent["system"]
    # follow-up keeps the earlier turns
    hist = [{"role": "user", "text": "What can this be?"}, {"role": "assistant", "text": r.json()["reply"]}]
    client.post("/api/chat", headers=h, json={"history_id": hid, "message": "And care tips?", "history": hist})
    assert [t["text"] for t in fake.calls[-1]["turns"]][0] == "What can this be?"
    assert fake.calls[-1]["turns"][-1]["text"] == "And care tips?"


def test_chat_endpoint_rules(client, fake):
    h1, h2 = signup(client, "chat2@x.com"), signup(client, "chat3@x.com")
    hid = client.post("/api/predict/oral", headers=h1, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()["id"]
    assert client.post("/api/chat", json={"history_id": hid, "message": "hi"}).status_code == 401
    assert client.post("/api/chat", headers=h2, json={"history_id": hid, "message": "hi"}).status_code == 404
    assert client.post("/api/chat", headers=h1, json={"history_id": hid, "message": "  "}).status_code == 400
    assert client.post("/api/chat", headers=h1, json={"history_id": 99999, "message": "hi"}).status_code == 404
    assert client.post("/api/chat", headers=h1, json={"history_id": hid, "message": "hi",
                                                      "history": [{"role": "user", "text": "x"}] * 41}).status_code == 400


def test_chat_failure_keeps_result_available(client, fake):
    h = signup(client, "chat4@x.com")
    hid = client.post("/api/predict/skin", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()["id"]
    fake.reply = RuntimeError("down")
    r = client.post("/api/chat", headers=h, json={"history_id": hid, "message": "hello"})
    assert r.status_code == 200 and r.json()["ok"] is False and r.json()["error"] == "unavailable"
    assert client.get(f"/api/history/{hid}", headers=h).status_code == 200     # CNN result is untouched


def test_chat_rate_limit(client, fake):
    h = signup(client, "chat5@x.com")
    hid = client.post("/api/predict/skin", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()["id"]
    codes = [client.post("/api/chat", headers=h, json={"history_id": hid, "message": "hi"}).status_code for _ in range(22)]
    assert codes[:20] == [200] * 20 and codes[20] == 429
