import pytest
from fastapi.testclient import TestClient

from app.db import DatabaseManager
from migrations import run_migrations
import app.main as main
import app.auth as auth_module
from app.auth import pwd_context

@pytest.mark.asyncio
async def test_save_and_delete_meeting(tmp_path):
    db_path = tmp_path / "test.db"
    await run_migrations(str(db_path))
    db = DatabaseManager(str(db_path))
    main.db = db
    main.processor.db = db
    auth_module.db = db
    await run_migrations(str(db_path))  # ensure tables exist for auth module as well (already done, but safe)
    await auth_module.db.create_user("admin", pwd_context.hash("adminpass"), "admin")
    await db.save_meeting("m1", "Initial")

    client = TestClient(main.app)
    token_resp = client.post("/token", data={"username": "admin", "password": "adminpass", "grant_type": "password"})
    access_token = token_resp.json()["access_token"]
    resp = client.post(
        "/save-meeting-title",
        json={"meeting_id": "m1", "title": "Updated"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    meeting = await db.get_meeting("m1")
    assert meeting["title"] == "Updated"

    resp = client.post(
        "/delete-meeting",
        json={"meeting_id": "m1"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    assert await db.get_meeting("m1") is None
