"""Risk, change-over-time, escalation, progress file and privacy tests. No Streamlit server, no internet."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import services as S  # noqa: E402
import triage  # noqa: E402


def entry(label="eczema", p=0.8, ts="2026-11-01T10:00:00", check="skin", status="ok", emb=None, bright=120, others=None):
    rest = others or {"acne": 1 - p}
    probs = [{"label": label, "p": p}] + [{"label": k, "p": v} for k, v in rest.items()]
    return {"ts": ts, "time": ts[:10], "check": check, "label": label, "confidence": p, "status": status,
            "probs": probs, "emb": emb, "brightness": bright, "quality": {"warnings": []}}


class Box(dict):
    """Stands in for st.session_state (attribute and item access)."""
    __getattr__ = dict.get
    def __setattr__(self, k, v): self[k] = v


# ------------------------------------------------------------------ risk
def test_no_answers_means_unknown_not_low():
    assert triage.risk_level({})["level"] == "unknown"


def test_tobacco_and_long_lasting_oral_problem_is_high():
    r = triage.risk_level({"tobacco": "Chewing (gutka, paan, tobacco)", "duration": "More than 4 weeks"}, "oral")
    assert r["level"] == "high" and "Tobacco use" in r["reasons"]


def test_changing_lesion_is_high_on_its_own():
    assert triage.risk_level({"changing": "Yes"}, "skin")["level"] == "high"


def test_sun_counts_for_skin_not_oral():
    assert triage.risk_level({"sun": "High (outdoor work, easy sunburn)", "age": "60 or more"}, "skin")["points"] == 2
    assert triage.risk_level({"sun": "High (outdoor work, easy sunburn)"}, "oral")["points"] == 0


# ------------------------------------------------------------------ compare
def test_first_check_has_no_comparison():
    assert triage.compare(None, entry())["has_prev"] is False


def test_same_result_gives_no_alert():
    c = triage.compare(entry(ts="2026-11-01T10:00:00"), entry(ts="2026-11-15T10:00:00", p=0.79),
                       [])
    assert not c["alert"] and c["tv"] < 0.05


def test_label_change_raises_alert_with_reason():
    prev = entry("normal", 0.85, others={"eczema": 0.15})
    cur = entry("eczema", 0.8, ts="2026-11-15T10:00:00", others={"normal": 0.2})
    c = triage.compare(prev, cur)
    assert c["alert"] and c["label_changed"] and any("changed from normal to eczema" in x for x in c["lines"])


def test_big_fingerprint_shift_raises_alert():
    a = [1.0] + [0.0] * 9
    b = [0.5, 0.86] + [0.0] * 8
    c = triage.compare(entry(emb=a), entry(emb=b, ts="2026-11-10T10:00:00"))
    assert c["emb"] > triage.EMB_ALERT and c["alert"]


def test_very_different_light_is_flagged_and_not_alone_an_alert():
    c = triage.compare(entry(bright=60), entry(bright=170, ts="2026-11-10T10:00:00"))
    assert c["lighting_differs"] and not c["alert"]


def test_mouth_ulcer_for_two_weeks_is_flagged():
    old = entry("mouth_ulcer", 0.9, ts="2026-11-01T09:00:00", check="oral", others={"calculus": 0.1})
    mid = entry("mouth_ulcer", 0.9, ts="2026-11-08T09:00:00", check="oral", others={"calculus": 0.1})
    new = entry("mouth_ulcer", 0.9, ts="2026-11-17T09:00:00", check="oral", others={"calculus": 0.1})
    c = triage.compare(mid, new, [old])
    assert c["persisting"] and c["alert"] and "2 to 3 weeks" in " ".join(c["lines"])


# ------------------------------------------------------------------ escalation
NO_CHANGE = {"alert": False, "persisting": False}
NO_RISK = {"level": "unknown", "reasons": []}


def test_blurry_photo_is_never_a_result():
    res = entry(); res["quality"] = {"warnings": ["blurry"]}
    n = triage.escalate(res, NO_RISK, NO_CHANGE)
    assert n["level"] == "retake" and "blurry" in " ".join(n["reasons"]).lower() and "see a doctor" in n["text"]


def test_low_confidence_retakes_but_high_risk_goes_to_doctor():
    res = entry(status="uncertain")
    assert triage.escalate(res, NO_RISK, NO_CHANGE)["level"] == "retake"
    high = {"level": "high", "reasons": ["Tobacco use"]}
    n = triage.escalate(res, high, NO_CHANGE, "dentist")
    assert n["level"] == "doctor" and "dentist" in n["text"] and "do not wait" in " ".join(n["reasons"])


def test_cancer_label_and_persisting_ulcer_go_to_doctor():
    assert triage.escalate(entry("SkinCancer", 0.9), NO_RISK, NO_CHANGE, urgent_label=True)["level"] == "doctor"
    assert triage.escalate(entry(), NO_RISK, {"alert": True, "persisting": True})["level"] == "doctor"


def test_normal_is_routine_and_non_normal_is_watch():
    assert triage.escalate(entry("normal", 0.9), NO_RISK, NO_CHANGE)["level"] == "routine"
    assert triage.escalate(entry("eczema", 0.8), NO_RISK, NO_CHANGE)["level"] == "watch"


def test_change_in_a_problem_goes_to_doctor():
    n = triage.escalate(entry("eczema", 0.8), NO_RISK, {"alert": True, "persisting": False})
    assert n["level"] == "doctor" and any("changed" in r for r in n["reasons"])


# ------------------------------------------------------------------ progress file and privacy
@pytest.fixture
def state(monkeypatch):
    box = Box(history=[], risk=dict(triage.DEFAULT_RISK), name="Prince")
    monkeypatch.setattr(S, "st", SimpleNamespace(session_state=box))
    return box


def test_export_has_no_photo_no_name_and_roundtrips(state):
    e = entry(emb=[0.1, 0.2]); e["thumb"] = object()
    state.history.append(e)
    raw = S.export_progress()
    assert "Prince" not in raw and "thumb" not in raw and "base64" not in raw
    state.history.clear()
    ok, msg = S.import_progress(raw.encode())
    assert ok and len(state.history) == 1 and state.history[0]["label"] == "eczema" and state.history[0]["thumb"] is None
    ok, _ = S.import_progress(raw.encode())                    # loading twice does not duplicate
    assert len(state.history) == 1


@pytest.mark.parametrize("raw", [b"not json", b"{}", b'{"app":"health-check","version":2,"entries":[]}',
                                 b'{"app":"health-check","version":1,"entries":[{"check":"skin"}],"risk":{}}',
                                 b"\xff\xfe", b"x" * 3_000_000])
def test_bad_files_are_rejected_without_crash(state, raw):
    ok, msg = S.import_progress(raw)
    assert not ok and state.history == [] and msg


def test_unknown_values_in_file_are_ignored(state):
    data = {"app": "health-check", "version": 1, "risk": {"tobacco": "<script>", "age": "60 or more"},
            "entries": [{"ts": "2026-11-01T10:00:00", "check": "hacker", "status": "ok", "label": "x",
                         "confidence": 1, "probs": []}]}
    ok, _ = S.import_progress(json.dumps(data).encode())
    assert ok and state.history == [] and state.risk["tobacco"] == "Prefer not to say" and state.risk["age"] == "60 or more"


def test_doctor_summary_has_disclaimer_and_no_photo(state):
    state.history.append({**entry(), "alert_lines": ["The result changed."], "next_step": "See a doctor soon"})
    text = S.summary_for_doctor()
    assert "not a diagnosis" in text and "ALERT: The result changed." in text and "Photos are not included" in text
