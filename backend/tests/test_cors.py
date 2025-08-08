import os
import sys
import importlib
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def create_app(monkeypatch, origins):
    monkeypatch.setenv("ALLOWED_ORIGINS", ",".join(origins))
    import app.main as main
    importlib.reload(main)
    return main.app


def test_allowed_origin(monkeypatch):
    app = create_app(monkeypatch, ["http://trusted.com"])
    client = TestClient(app)
    response = client.options(
        "/get-meetings",
        headers={
            "Origin": "http://trusted.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://trusted.com"


def test_blocked_origin(monkeypatch):
    app = create_app(monkeypatch, ["http://trusted.com"])
    client = TestClient(app)
    response = client.options(
        "/get-meetings",
        headers={
            "Origin": "http://malicious.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
