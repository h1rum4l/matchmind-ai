from pathlib import Path
import json
import pytest

AppTest = pytest.importorskip("streamlit.testing.v1", reason="optional legacy UI").AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_forecast_and_same_team_validation():
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 3
    probabilities = [float(metric.value.rstrip("%")) for metric in app.metric]
    assert abs(sum(probabilities) - 100) < 0.2
    app.selectbox[1].select(app.selectbox[0].value)
    app.button[0].click().run()
    assert not app.exception
    assert app.warning
    assert len(app.metric) == 0
    app.selectbox[1].select("Liverpool")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 3


def test_missing_model_shows_recovery(monkeypatch):
    original = Path.read_bytes

    def read(path):
        if path == ROOT / "models/model.json":
            raise FileNotFoundError("model missing")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert app.error
    assert "matchmind.train" in app.code[0].value


def test_stale_model_rejected(monkeypatch):
    original = Path.read_bytes

    def read(path):
        content = original(path)
        if path == ROOT / "models/model.json":
            model = json.loads(content)
            model["data_csv_sha256"] = "outdated"
            return json.dumps(model).encode()
        return content

    monkeypatch.setattr(Path, "read_bytes", read)
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert "different data" in app.error[0].value
