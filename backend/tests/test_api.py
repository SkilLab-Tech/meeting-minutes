import pytest
from fastapi.testclient import TestClient

from db import DatabaseManager
import main

@pytest.mark.asyncio
async def test_save_and_delete_meeting(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    main.db = db
    main.processor.db = db
    await db.save_meeting("m1", "Initial")

    client = TestClient(main.app)
    resp = client.post("/save-meeting-title", json={"meeting_id": "m1", "title": "Updated"})
    assert resp.status_code == 200
    meeting = await db.get_meeting("m1")
    assert meeting["title"] == "Updated"

    resp = client.post("/delete-meeting", json={"meeting_id": "m1"})
    assert resp.status_code == 200
    assert await db.get_meeting("m1") is None
