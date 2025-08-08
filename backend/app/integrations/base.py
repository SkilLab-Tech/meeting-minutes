import requests
from urllib.parse import urlencode

from ..config import FeatureFlags

class OAuthConnector:
    """Base class for OAuth based connectors."""
    auth_base_url: str = ""
    token_url: str = ""
    api_base_url: str = ""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, *, enabled: bool):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.enabled = enabled

    def authorization_url(self, scope: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope,
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()

    def join_meeting(self, meeting_id: str, token: str) -> dict:
        raise NotImplementedError
