import asyncio
import os
import sys

import os
import sys
import asyncio

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import app.main as main
import app.auth as auth_module
from app.auth import pwd_context

client = TestClient(main.app)


async def _create_user(username: str, password: str, role: str):
    await auth_module.db.create_user(username, pwd_context.hash(password), role)


@pytest.fixture(autouse=True)
def setup_users(test_db):
    asyncio.run(_create_user("alice", "wonderland", "user"))
    asyncio.run(_create_user("admin", "adminpass", "admin"))


def login(username: str, password: str):
    return client.post(
        "/token",
        data={"username": username, "password": password, "grant_type": "password"},
    )


def test_login():
    response = login("alice", "wonderland")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token():
    tokens = login("alice", "wonderland").json()
    response = client.post("/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_role_enforcement():
    user_tokens = login("alice", "wonderland").json()
    res_user = client.post(
        "/delete-meeting",
        json={"meeting_id": "1"},
        headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
    )
    assert res_user.status_code == 403

    admin_tokens = login("admin", "adminpass").json()
    res_admin = client.post(
        "/delete-meeting",
        json={"meeting_id": "1"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert res_admin.status_code == 200
