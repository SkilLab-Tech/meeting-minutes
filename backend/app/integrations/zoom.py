import requests

from .base import OAuthConnector
from ..config import FeatureFlags

class ZoomConnector(OAuthConnector):
    """Zoom integration using OAuth"""
    auth_base_url = "https://zoom.us/oauth/authorize"
    token_url = "https://zoom.us/oauth/token"
    api_base_url = "https://api.zoom.us/v2"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri, enabled=FeatureFlags.zoom_enabled())

    def join_meeting(self, meeting_id: str, token: str) -> dict:
        if not self.enabled:
            raise RuntimeError("Zoom integration disabled")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.api_base_url}/meetings/{meeting_id}/join"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
