from unittest import mock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.meeting_bot import MeetingBot


def test_meeting_bot_flow(monkeypatch):
    connector = mock.MagicMock()
    transcriber = mock.MagicMock(return_value="transcript")
    bot = MeetingBot(connector, transcriber)
    result = bot.join_record_and_transcribe("123", "token")
    connector.join_meeting.assert_called_once_with("123", "token")
    transcriber.assert_called_once()
    assert result == "transcript"
