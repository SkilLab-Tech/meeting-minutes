"""Pydantic models for meeting-related operations."""

from typing import List, Optional

from pydantic import BaseModel


class Transcript(BaseModel):
    id: str
    text: str
    timestamp: str


class MeetingResponse(BaseModel):
    id: str
    title: str


class MeetingDetailsResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    transcripts: List[Transcript]


class MeetingTitleUpdate(BaseModel):
    title: str


class MeetingTitleRequest(MeetingTitleUpdate):
    meeting_id: str


class SaveTranscriptRequest(BaseModel):
    meeting_title: str
    transcripts: List[Transcript]


class SaveModelConfigRequest(BaseModel):
    provider: str
    model: str
    whisperModel: str
    apiKey: Optional[str] = None


class TranscriptRequest(BaseModel):
    """Request model for transcript text"""

    text: str
    model: str
    model_name: str
    chunk_size: Optional[int] = 5000
    overlap: Optional[int] = 1000


class ProcessTranscriptRequest(TranscriptRequest):
    meeting_id: str


class AsyncSummaryRequest(BaseModel):
    """Request model for asynchronous summary generation"""

    text: str


class DeleteMeetingRequest(BaseModel):
    meeting_id: str

