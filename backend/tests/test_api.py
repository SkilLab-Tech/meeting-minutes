import pytest
from fastapi.testclient import TestClient

from db import DatabaseManager
import main
from auth import db as auth_db, pwd_context

@pytest.mark.asyncio
async def test_update_and_delete_meeting(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    main.db = db
    main.processor.db = db
    await db.save_meeting("m1", "Initial")

    # Create admin user for authentication
    await auth_db.create_user("admin_api", pwd_context.hash("adminpass"), "admin")

    client = TestClient(main.app)
    tokens = client.post(
        "/token",
        data={"username": "admin_api", "password": "adminpass", "grant_type": "password"},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post("/meetings/m1/title", json={"title": "Updated"}, headers=headers)
    assert resp.status_code == 200
    meeting = await db.get_meeting("m1")
    assert meeting["title"] == "Updated"

    resp = client.delete("/meetings/m1", headers=headers)
    assert resp.status_code == 200
    assert await db.get_meeting("m1") is None
