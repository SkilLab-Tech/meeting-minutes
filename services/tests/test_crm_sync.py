"""Tests for :mod:`services.crm_sync`.

These tests mock out network calls so no actual HTTP requests are sent.
"""

from __future__ import annotations

from typing import Any, Dict
import os
import sys

import httpx
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


@pytest.mark.asyncio
async def test_salesforce_push_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    calls = {"count": 0}

    async def fake_post(self, url, json, headers, timeout):  # type: ignore[override]
        calls["count"] += 1
        if calls["count"] < 3:
            raise httpx.RequestError("boom", request=httpx.Request("POST", url))

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

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = await sync.push_to_salesforce(MEETING)

    assert result == {"id": 1}
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_hubspot_push_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    async def fake_post(self, url, json, headers, timeout):  # type: ignore[override]
        raise httpx.HTTPError("bad")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(httpx.HTTPError):
        await sync.push_to_hubspot(MEETING)


@pytest.mark.asyncio
async def test_pipedrive_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _make_config()
    sync = CRMSync(config)

    captured: Dict[str, Any] = {}

    async def fake_post(self, url, json, headers, timeout):  # type: ignore[override]
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

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    await sync.push_to_pipedrive(MEETING)

    assert captured["url"] == config.pipedrive_url
    assert captured["headers"] == {"Authorization": f"Bearer {config.pipedrive_api_key}"}
    assert captured["json"] == {
        "title": MEETING["title"],
        "date": MEETING["date"],
        "participants": "alice,bob",
    }

