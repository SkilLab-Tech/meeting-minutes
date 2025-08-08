import os
import sys

os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'true'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

@pytest.mark.skip(reason="Celery workflow requires full worker setup")
def test_async_summary_workflow():
    response = client.post('/summary/async', json={'text': 'hello\nworld'})
    assert response.status_code == 200
    task_id = response.json()['task_id']

    result_response = client.get(f'/summary/async/{task_id}')
    assert result_response.status_code == 200
    data = result_response.json()
    assert data['status'] == 'completed'
    assert data['result']['line_count'] == 2
