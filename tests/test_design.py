"""Guard the deliverable's offline photos, attribution and native-app recovery."""
import base64
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class PhotoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.photos = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.photos.append(dict(attrs))


def test_preview_has_offline_real_photos_and_credits():
    document = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = PhotoParser()
    parser.feed(document)
    assert len(parser.photos) == 2
    for photo, filename in zip(parser.photos, ["haaland.jpg", "salah.png"]):
        assert photo["alt"]
        assert photo["src"].startswith("data:image/")
        assert base64.b64decode(photo["src"].split(",", 1)[1]) == (ROOT / "assets" / filename).read_bytes()
    assert "Jacek Stanislawek" in document
    assert "Mohamed Salah" in document
    assert "user-supplied" in document
    assert "creativecommons.org/licenses/by-sa/4.0/" in document


def test_motion_remains_optional():
    document = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "@media(prefers-reduced-motion:reduce)" in document
    assert "animation:none!important" in document
    assert "if (motion.matches || document.querySelector('#mm-pause').checked) return" in document
    assert 'type="checkbox" id="mm-pause"' in document
    assert "console.warn('MatchMind: GPU animation unavailable" in document


def test_missing_design_file_shows_recovery(monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1", reason="optional legacy UI").AppTest
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path == ROOT / "index.html":
            raise FileNotFoundError("design missing")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert "design missing" in app.error[0].value
    assert len(app.metric) == 0


def test_truncated_design_shows_recovery(monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1", reason="optional legacy UI").AppTest
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path == ROOT / "index.html":
            return "<html>truncated download</html>"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert "Design preview is incomplete" in app.error[0].value
