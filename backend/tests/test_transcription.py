import json
import pytest

import transcript_processor as tp_module
from transcript_processor import TranscriptProcessor, Section, SummaryResponse

class DummyDB:
    async def get_api_key(self, provider):
        return "key"

class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass
    async def run(self, prompt):
        result = SummaryResponse(
            MeetingName="Test Meeting",
            SectionSummary=Section(title="Section Summary", blocks=[]),
            CriticalDeadlines=Section(title="Critical Deadlines", blocks=[]),
            KeyItemsDecisions=Section(title="Key Items & Decisions", blocks=[]),
            ImmediateActionItems=Section(title="Immediate Action Items", blocks=[]),
            NextSteps=Section(title="Next Steps", blocks=[]),
            OtherImportantPoints=Section(title="Other Important Points", blocks=[]),
            ClosingRemarks=Section(title="Closing Remarks", blocks=[]),
        )
        class R:
            data = result
        return R()

@pytest.mark.asyncio
async def test_process_transcript(monkeypatch):
    monkeypatch.setattr(tp_module, "db", DummyDB())
    monkeypatch.setattr(tp_module, "Agent", DummyAgent)
    processor = TranscriptProcessor()
    num_chunks, data = await processor.process_transcript("hello world", "openai", "gpt-test", 10, 0)
    assert num_chunks == 2
    assert len(data) == 2
    summary = json.loads(data[0])
    assert summary["MeetingName"] == "Test Meeting"
