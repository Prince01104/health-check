"""API tests with the random demo models. Run from the project folder:  python -m pytest -q"""
import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

TMP = tempfile.mkdtemp(prefix="hc_test_")
os.environ["HC_DATA_DIR"] = str(Path(TMP) / "data")
os.environ["HC_MODELS_DIR"] = str(Path(TMP) / "models")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import make_dummy_models  # noqa: E402

make_dummy_models.main(Path(os.environ["HC_MODELS_DIR"]))
# registry.json lives in the real models folder; copy it next to the temp models
(Path(TMP) / "models" / "registry.json").write_text((ROOT / "models" / "registry.json").read_text())

from backend.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def photo(kind="ok"):
    """Make a test photo. kind: ok | blurry | dark | tiny"""
    size = (60, 60) if kind == "tiny" else (480, 360)
    img = Image.new("RGB", size, (200, 140, 120))
    d = ImageDraw.Draw(img)
    for i in range(0, size[0], 12):
        d.rectangle([i, 0, i + 5, size[1]], fill=(230, 200, 190))
    if kind == "dark":
        img = Image.new("RGB", size, (10, 10, 10))
    if kind == "blurry":
        from PIL import ImageFilter
        img = Image.new("RGB", size, (200, 140, 120)).filter(ImageFilter.GaussianBlur(5))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def signup(client, email="a@b.com", name="Prince"):
    r = client.post("/api/signup", json={"name": name, "email": email, "password": "secret1"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def test_checks_public(client):
    r = client.get("/api/checks")
    assert r.status_code == 200
    by = {c["id"]: c for c in r.json()}
    assert by["oral"]["ready"] and by["skin"]["ready"]
    assert not by["infection"]["ready"] and not by["nail"]["ready"]
    assert by["oral"]["demo"] is True


def test_auth_flow(client):
    h = signup(client)
    assert client.get("/api/me", headers=h).json()["name"] == "Prince"
    assert client.post("/api/signup", json={"name": "x", "email": "a@b.com", "password": "secret1"}).status_code == 409
    assert client.post("/api/signup", json={"name": "x", "email": "bad", "password": "secret1"}).status_code == 400
    assert client.post("/api/signup", json={"name": "x", "email": "c@d.com", "password": "123"}).status_code == 400
    assert client.post("/api/login", json={"email": "a@b.com", "password": "wrong!"}).status_code == 401
    assert client.post("/api/login", json={"email": "a@b.com", "password": "secret1"}).status_code == 200
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert client.post("/api/logout", headers=h).status_code == 200
    assert client.get("/api/me", headers=h).status_code == 401


def test_predict_history_report(client):
    h = signup(client, "p@q.com")
    r = client.post("/api/predict/oral", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")})
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["check"] == "oral" and res["demo"] is True
    assert res["status"] in ("ok", "uncertain")
    assert abs(sum(p["p"] for p in res["probs"]) - 1) < 0.01
    assert res["content"]["en"]["tips"] and res["content"]["hi"]["tips"]
    hid = res["id"]
    assert client.get(f"/api/history/{hid}/image?kind=img", headers=h).headers["content-type"].startswith("image/")
    if res["has_heatmap"]:
        assert client.get(f"/api/history/{hid}/image?kind=heat", headers=h).status_code == 200
    pdf = client.get(f"/api/history/{hid}/report", headers=h)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    lst = client.get("/api/history", headers=h).json()
    assert [x["id"] for x in lst] == [hid]
    me = client.get("/api/me?tz=330", headers=h).json()["stats"]
    assert me["total"] == 1 and me["streak"] == 1 and me["today_done"] is True
    # skin check works too
    r2 = client.post("/api/predict/skin", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")})
    assert r2.status_code == 200 and r2.json()["check"] == "skin"
    assert len(client.get("/api/history?check=skin", headers=h).json()) == 1


def test_quality_warnings(client):
    h = signup(client, "q@q.com")
    for kind, warn in [("dark", "dark"), ("blurry", "blurry"), ("tiny", "low_res")]:
        r = client.post("/api/predict/oral", headers=h, files={"file": ("a.jpg", photo(kind), "image/jpeg")})
        assert r.status_code == 200, r.text
        assert warn in r.json()["quality"]["warnings"], (kind, r.json()["quality"])


def test_bad_inputs(client):
    h = signup(client, "r@r.com")
    assert client.post("/api/predict/oral", files={"file": ("a.jpg", photo(), "image/jpeg")}).status_code == 401
    assert client.post("/api/predict/oral", headers=h, files={"file": ("a.txt", b"not an image", "text/plain")}).status_code == 400
    assert client.post("/api/predict/nail", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).status_code == 503
    assert client.post("/api/predict/bogus", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).status_code == 404
    big = b"\xff\xd8" + b"0" * (11 * 1024 * 1024)
    assert client.post("/api/predict/oral", headers=h, files={"file": ("a.jpg", big, "image/jpeg")}).status_code == 413


def test_users_cannot_see_each_others_results(client):
    h1 = signup(client, "u1@x.com")
    h2 = signup(client, "u2@x.com")
    hid = client.post("/api/predict/oral", headers=h1, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()["id"]
    for path in (f"/api/history/{hid}", f"/api/history/{hid}/image", f"/api/history/{hid}/report"):
        assert client.get(path, headers=h2).status_code == 404
    assert client.delete(f"/api/history/{hid}", headers=h2).status_code == 404
    assert client.get(f"/api/history/{hid}", headers=h1).status_code == 200


def test_delete_history_and_account(client):
    h = signup(client, "d@d.com")
    ids = [client.post("/api/predict/oral", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")}).json()["id"]
           for _ in range(2)]
    assert client.delete(f"/api/history/{ids[0]}", headers=h).status_code == 200
    assert len(client.get("/api/history", headers=h).json()) == 1
    assert client.delete("/api/history", headers=h).json()["deleted"] == 1
    client.post("/api/predict/oral", headers=h, files={"file": ("a.jpg", photo(), "image/jpeg")})
    assert client.delete("/api/me", headers=h).status_code == 200
    assert client.get("/api/me", headers=h).status_code == 401
    assert client.post("/api/login", json={"email": "d@d.com", "password": "secret1"}).status_code == 401
    # no photo files left behind for the deleted user
    from backend import db
    left = [p.name for p in db.UPLOADS.iterdir() if p.name.split("_")[0] in {str(i) for i in ids}]
    assert left == [], left


def test_tip_and_index(client):
    t = client.get("/api/tip").json()
    assert t["en"] and t["hi"]
    r = client.get("/")
    assert r.status_code == 200 and "html" in r.headers["content-type"]
