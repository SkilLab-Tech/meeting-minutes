"""CRM synchronization utilities.

This module provides helpers to push meeting data to various CRM systems
including Salesforce, HubSpot and Pipedrive. Each integration supports
basic retry logic and raises an exception when the remote service cannot
be reached after the configured number of attempts.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict
import os

import httpx


@dataclass
class CRMConfig:
    """Configuration for CRM integrations.

    The configuration pulls API keys and endpoint URLs from environment
    variables so they can be easily customised without modifying code.
    HTTP requests use ``httpx.AsyncClient`` and run asynchronously.
    """

    salesforce_api_key: str
    salesforce_url: str
    hubspot_api_key: str
    hubspot_url: str
    pipedrive_api_key: str
    pipedrive_url: str
    max_retries: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "CRMConfig":
        """Construct a :class:`CRMConfig` from environment variables."""

        return cls(
            salesforce_api_key=os.getenv("SALESFORCE_API_KEY", ""),
            salesforce_url=os.getenv("SALESFORCE_URL", ""),
            hubspot_api_key=os.getenv("HUBSPOT_API_KEY", ""),
            hubspot_url=os.getenv("HUBSPOT_URL", ""),
            pipedrive_api_key=os.getenv("PIPEDRIVE_API_KEY", ""),
            pipedrive_url=os.getenv("PIPEDRIVE_URL", ""),
        )


class CRMSync:
    """Push meeting information to CRMs."""

    def __init__(self, config: CRMConfig | None = None) -> None:
        self.config = config or CRMConfig.from_env()

    # Public API -----------------------------------------------------------------
    async def push_to_salesforce(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._map_salesforce(meeting)
        headers = {"Authorization": f"Bearer {self.config.salesforce_api_key}"}
        return await self._post(self.config.salesforce_url, payload, headers)

    async def push_to_hubspot(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._map_hubspot(meeting)
        headers = {"Authorization": f"Bearer {self.config.hubspot_api_key}"}
        return await self._post(self.config.hubspot_url, payload, headers)

    async def push_to_pipedrive(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._map_pipedrive(meeting)
        headers = {"Authorization": f"Bearer {self.config.pipedrive_api_key}"}
        return await self._post(self.config.pipedrive_url, payload, headers)

    # Internal helpers -----------------------------------------------------------
    async def _post(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        delay = self.config.retry_delay
        async with httpx.AsyncClient() as client:
            for attempt in range(1, self.config.max_retries + 1):
                try:
                    response = await client.post(
                        url, json=payload, headers=headers, timeout=5
                    )
                    response.raise_for_status()
                    return response.json() if response.content else {}
                except httpx.HTTPError:
                    if attempt == self.config.max_retries:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2

        return {}

    @staticmethod
    def _map_salesforce(meeting: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "Subject": meeting.get("title"),
            "StartDate": meeting.get("date"),
            "Participants__c": ",".join(meeting.get("participants", [])),
        }

    @staticmethod
    def _map_hubspot(meeting: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "properties": {
                "meeting_title": meeting.get("title"),
                "meeting_date": meeting.get("date"),
                "participants": ",".join(meeting.get("participants", [])),
            }
        }

    @staticmethod
    def _map_pipedrive(meeting: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": meeting.get("title"),
            "date": meeting.get("date"),
            "participants": ",".join(meeting.get("participants", [])),
        }

