"""Tests for :mod:`services.crm_sync`.

These tests mock out network calls so no actual HTTP requests are sent.
"""

from __future__ import annotations

from typing import Any, Dict
import os
import sys

import requests
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.crm_sync import CRMConfig, CRMSync


MEETING: Dict[str, Any] = {
    "title": "Sync meeting",
    "date": "2024-01-01",
    "participants": ["alice", "bob"],
}


def _make_config() -> CRMConfig:
    return CRMConfig(
        salesforce_api_key="sf", salesforce_url="https://sf.example/api",
        hubspot_api_key="hs", hubspot_url="https://hs.example/api",
        pipedrive_api_key="pd", pipedrive_url="https://pd.example/api",
        max_retries=3, retry_delay=0.01,
    )


def test_salesforce_push_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    calls = {"count": 0}

    def fake_post(url, json, headers, timeout):  # type: ignore[override]
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.ConnectionError("boom")

        class Resp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self) -> Dict[str, Any]:
                return {"id": 1}

            @property
            def content(self) -> bytes:
                return b"{}"

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    result = sync.push_to_salesforce(MEETING)

    assert result == {"id": 1}
    assert calls["count"] == 3


def test_hubspot_push_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    def fake_post(url, json, headers, timeout):  # type: ignore[override]
        raise requests.HTTPError("bad")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.HTTPError):
        sync.push_to_hubspot(MEETING)


def test_pipedrive_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    captured = {}

    def fake_post(url, json, headers, timeout):  # type: ignore[override]
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers

        class Resp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self) -> Dict[str, Any]:
                return {"success": True}

            @property
            def content(self) -> bytes:
                return b"{}"

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    sync.push_to_pipedrive(MEETING)

    assert captured["url"] == config.pipedrive_url
    assert captured["headers"] == {"Authorization": f"Bearer {config.pipedrive_api_key}"}
    assert captured["json"] == {
        "title": MEETING["title"],
        "date": MEETING["date"],
        "participants": "alice,bob",
    }

