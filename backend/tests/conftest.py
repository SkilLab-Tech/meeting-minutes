import sys
import pathlib
import pytest

# Add backend/app to Python path
APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"
sys.path.append(str(APP_DIR))

import db as db_module
import main as main_module

@pytest.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    database = db_module.DatabaseManager(str(db_path))
    main_module.db = database
    main_module.processor.db = database
    return database

@pytest.fixture
async def client(test_db):
    from fastapi.testclient import TestClient
    return TestClient(main_module.app)
