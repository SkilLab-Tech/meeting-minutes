import pytest
import main
from auth import (
    User,
    get_current_active_user,
    get_current_active_admin,
    get_current_user,
)


@pytest.mark.asyncio
async def test_get_meetings_success(client, test_db):
    await test_db.save_meeting("m1", "Meeting 1")

    async def override_user():
        return User(username="tester", role="user")

    main.app.dependency_overrides[get_current_active_user] = override_user
    response = client.get("/get-meetings")
    assert response.status_code == 200
    assert response.json() == [{"id": "m1", "title": "Meeting 1"}]
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_meetings_error(client, test_db, monkeypatch):
    async def override_user():
        return User(username="tester", role="user")

    main.app.dependency_overrides[get_current_active_user] = override_user

    async def mock_get_all_meetings():
        raise Exception("DB error")

    monkeypatch.setattr(main.db, "get_all_meetings", mock_get_all_meetings)
    response = client.get("/get-meetings")
    assert response.status_code == 500
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_meeting_by_id_success(client, test_db):
    await test_db.save_meeting("m1", "Meeting 1")
    await test_db.save_meeting_transcript("m1", "hello", "2024-01-01T00:00:00Z")

    response = client.get("/meetings/m1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "m1"
    assert data["title"] == "Meeting 1"
    assert len(data["transcripts"]) == 1


@pytest.mark.asyncio
async def test_get_meeting_by_id_not_found(client):
    response = client.get("/meetings/unknown")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_meeting_summary_success(client, test_db):
    await test_db.save_meeting("m1", "Meeting 1")
    await test_db.create_process("m1")
    await test_db.update_process("m1", status="COMPLETED", result={"MeetingName": "Meeting 1"})
    await test_db.save_transcript("m1", "text", "model", "model-name", 10, 0)

    response = client.get("/meetings/m1/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["data"]["MeetingName"] == "Meeting 1"


@pytest.mark.asyncio
async def test_get_meeting_summary_not_found(client):
    response = client.get("/meetings/unknown/summary")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_save_meeting_title_success(client, test_db):
    await test_db.save_meeting("m1", "Old Title")

    async def override_admin():
        return User(username="admin", role="admin")

    main.app.dependency_overrides[get_current_active_admin] = override_admin
    response = client.post(
        "/save-meeting-title", json={"meeting_id": "m1", "title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Meeting title saved successfully"}

    meeting = await test_db.get_meeting("m1")
    assert meeting["title"] == "Updated"
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_save_meeting_title_db_error(client, test_db, monkeypatch):
    await test_db.save_meeting("m1", "Old Title")

    async def override_admin():
        return User(username="admin", role="admin")

    main.app.dependency_overrides[get_current_active_admin] = override_admin

    async def mock_update_meeting_title(meeting_id, title):
        raise Exception("DB error")

    monkeypatch.setattr(main.db, "update_meeting_title", mock_update_meeting_title)
    response = client.post(
        "/save-meeting-title", json={"meeting_id": "m1", "title": "Updated"}
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "DB error"
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_meeting_success(client, test_db):
    await test_db.save_meeting("m1", "Meeting 1")

    async def override_admin():
        return User(username="admin", role="admin")

    main.app.dependency_overrides[get_current_active_admin] = override_admin
    response = client.post("/delete-meeting", json={"meeting_id": "m1"})
    assert response.status_code == 200
    assert response.json() == {"message": "Meeting deleted successfully"}

    meeting = await test_db.get_meeting("m1")
    assert meeting is None
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_meeting_non_admin_forbidden(client, test_db):
    await test_db.save_meeting("m1", "Meeting 1")

    async def override_user():
        return User(username="tester", role="user")

    main.app.dependency_overrides[get_current_user] = override_user
    response = client.post("/delete-meeting", json={"meeting_id": "m1"})
    assert response.status_code in (401, 403)

    meeting = await test_db.get_meeting("m1")
    assert meeting is not None
    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_meeting_db_error(client, test_db, monkeypatch):
    await test_db.save_meeting("m1", "Meeting 1")

    async def override_admin():
        return User(username="admin", role="admin")

    main.app.dependency_overrides[get_current_active_admin] = override_admin

    async def mock_delete_meeting(meeting_id):
        raise Exception("DB error")

    monkeypatch.setattr(main.db, "delete_meeting", mock_delete_meeting)
    response = client.post("/delete-meeting", json={"meeting_id": "m1"})
    assert response.status_code == 500
    assert response.json()["detail"] == "DB error"
    main.app.dependency_overrides.clear()

