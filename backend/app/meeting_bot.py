import os
import tempfile
from typing import Callable

class MeetingBot:
    """Bot that joins meetings, records audio and hands off for transcription."""
    def __init__(self, connector, transcriber: Callable[[str], str]):
        self.connector = connector
        self.transcriber = transcriber

    def join_meeting(self, meeting_id: str, token: str) -> None:
        self.connector.join_meeting(meeting_id, token)

    def record_audio(self, duration: int = 1) -> str:
        """Simulate audio recording by creating an empty temp file."""
        fd, path = tempfile.mkstemp(suffix=".wav")
        with os.fdopen(fd, "wb") as f:
            f.write(b"")
        return path

    def handoff_for_transcription(self, audio_path: str) -> str:
        return self.transcriber(audio_path)

    def join_record_and_transcribe(self, meeting_id: str, token: str) -> str:
        self.join_meeting(meeting_id, token)
        audio = self.record_audio()
        return self.handoff_for_transcription(audio)
