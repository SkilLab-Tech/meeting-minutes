import os
from dataclasses import dataclass

@dataclass
class ConnectorConfig:
    """Configuration for OAuth connectors."""
    client_id: str
    client_secret: str
    redirect_uri: str

class FeatureFlags:
    """Feature flags toggling integrations."""
    @staticmethod
    def zoom_enabled() -> bool:
        return os.getenv("FEATURE_ZOOM", "false").lower() == "true"

    @staticmethod
    def google_meet_enabled() -> bool:
        return os.getenv("FEATURE_GOOGLE_MEET", "false").lower() == "true"
