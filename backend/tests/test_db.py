import pytest

from app.db import DatabaseManager
from migrations import run_migrations

@pytest.mark.asyncio
async def test_meeting_crud(tmp_path):
    db_path = tmp_path / "test.db"
    await run_migrations(str(db_path))
    db = DatabaseManager(str(db_path))

    await db.save_meeting("m1", "Test Meeting")
    meeting = await db.get_meeting("m1")
    assert meeting["title"] == "Test Meeting"

    await db.save_meeting_transcript("m1", "hello", "2021-01-01T00:00:00Z")
    meeting = await db.get_meeting("m1")
    assert len(meeting["transcripts"]) == 1

    await db.delete_meeting("m1")
    assert await db.get_meeting("m1") is None
