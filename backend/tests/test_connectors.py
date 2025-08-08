import json
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.integrations.zoom import ZoomConnector
from app.integrations.google import GoogleMeetConnector


def _fake_response(payload):
    class Resp:
        def raise_for_status(self):
            pass
        def json(self):
            return payload
    return Resp()


def test_zoom_exchange_code(monkeypatch):
    monkeypatch.setenv("FEATURE_ZOOM", "true")
    connector = ZoomConnector("id", "secret", "http://localhost")
    monkeypatch.setattr("app.integrations.base.requests.post", lambda *a, **k: _fake_response({"access_token": "abc"}))
    token = connector.exchange_code_for_token("code")
    assert token["access_token"] == "abc"


def test_google_exchange_code(monkeypatch):
    monkeypatch.setenv("FEATURE_GOOGLE_MEET", "true")
    connector = GoogleMeetConnector("id", "secret", "http://localhost")
    monkeypatch.setattr("app.integrations.base.requests.post", lambda *a, **k: _fake_response({"access_token": "xyz"}))
    token = connector.exchange_code_for_token("code")
    assert token["access_token"] == "xyz"


def test_zoom_disabled(monkeypatch):
    monkeypatch.setenv("FEATURE_ZOOM", "false")
    connector = ZoomConnector("id", "secret", "http://localhost")
    with mock.patch("app.integrations.zoom.requests.post"):
        try:
            connector.join_meeting("123", "token")
        except RuntimeError:
            assert True
        else:
            assert False
