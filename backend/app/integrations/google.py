import requests

from .base import OAuthConnector
from ..config import FeatureFlags

class GoogleMeetConnector(OAuthConnector):
    """Google Meet integration using OAuth"""
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    api_base_url = "https://meet.googleapis.com/v1"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri, enabled=FeatureFlags.google_meet_enabled())

    def join_meeting(self, meeting_id: str, token: str) -> dict:
        if not self.enabled:
            raise RuntimeError("Google Meet integration disabled")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.api_base_url}/meetings/{meeting_id}:join"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
