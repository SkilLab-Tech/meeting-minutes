class TranscriptService:
    """Service responsible for basic transcript processing."""

    def split_lines(self, text: str) -> list[str]:
        """Split the transcript into individual lines."""
        return [line.strip() for line in text.splitlines() if line.strip()]
