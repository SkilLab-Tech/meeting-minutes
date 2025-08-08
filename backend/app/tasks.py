from .celery_app import celery_app
from .services.transcript_service import TranscriptService
from .services.summary_service import SummaryService

_transcript_service = TranscriptService()
_summary_service = SummaryService()

@celery_app.task
def generate_summary_task(text: str) -> dict:
    """Celery task to process transcript text and generate a summary."""
    lines = _transcript_service.split_lines(text)
    return _summary_service.generate(lines)
