import sys
import pathlib
import pytest_asyncio

# Add backend to Python path so app package is importable
BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

import app.db as db_module
import app.main as main_module
sys.modules["db"] = db_module
sys.modules["main"] = main_module
import app.auth as auth_module
sys.modules["auth"] = auth_module
import app.transcript_processor as tp_module
sys.modules["transcript_processor"] = tp_module

@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    database = db_module.DatabaseManager(str(db_path))
    main_module.db = database
    main_module.processor.db = database
    return database

@pytest_asyncio.fixture
async def client(test_db):
    from fastapi.testclient import TestClient
    return TestClient(main_module.app)
