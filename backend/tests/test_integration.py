import json
import pytest
from fastapi.testclient import TestClient

import main
from main import TranscriptRequest, process_transcript_background
from db import DatabaseManager

@pytest.mark.asyncio
async def test_end_to_end_processing(tmp_path, monkeypatch):
    db = DatabaseManager(str(tmp_path / "test.db"))
    main.db = db
    main.processor.db = db

    async def fake_process_transcript(text, model, model_name, chunk_size, overlap):
        summary = {
            "MeetingName": "Integration Meeting",
            "SectionSummary": {"title": "Section Summary", "blocks": []},
            "CriticalDeadlines": {"title": "Critical Deadlines", "blocks": []},
            "KeyItemsDecisions": {"title": "Key Items & Decisions", "blocks": []},
            "ImmediateActionItems": {"title": "Immediate Action Items", "blocks": []},
            "NextSteps": {"title": "Next Steps", "blocks": []},
            "OtherImportantPoints": {"title": "Other Important Points", "blocks": []},
            "ClosingRemarks": {"title": "Closing Remarks", "blocks": []}
        }
        return 1, [json.dumps(summary)]

    monkeypatch.setattr(main.processor, "process_transcript", fake_process_transcript)

    client = TestClient(main.app)
    payload = {
        "text": "hello world",
        "model": "openai",
        "model_name": "gpt-test",
        "chunk_size": 10,
        "overlap": 0,
    }
    resp = client.post("/meetings/m1/summary", json=payload)
    assert resp.status_code == 200
    process_id = resp.json()["process_id"]

    await process_transcript_background(process_id, "m1", TranscriptRequest(**payload))

    resp = client.get("/meetings/m1/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["meetingName"] == "Integration Meeting"
