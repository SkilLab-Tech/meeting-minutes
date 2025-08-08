"""Router module containing meeting-related endpoints."""

import json
import logging
import time
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse

from auth import User, get_current_active_admin, get_current_active_user
from db import DatabaseManager
from schemas.meetings import (
    DeleteMeetingRequest,
    MeetingDetailsResponse,
    MeetingResponse,
    MeetingTitleRequest,
    MeetingTitleUpdate,
    ProcessTranscriptRequest,
    SaveTranscriptRequest,
    Transcript,
    TranscriptRequest,
)
from transcript_processor import TranscriptProcessor


logger = logging.getLogger(__name__)

router = APIRouter()


class SummaryProcessor:
    """Handles the processing of summaries in a thread-safe way."""

    def __init__(self) -> None:
        try:
            self.db = DatabaseManager()
            logger.info("Initializing SummaryProcessor components")
            self.transcript_processor = TranscriptProcessor()
            logger.info("SummaryProcessor initialized successfully (core components)")
        except Exception as e:  # pragma: no cover - initialization errors are logged
            logger.error(f"Failed to initialize SummaryProcessor: {str(e)}", exc_info=True)
            raise

    async def process_transcript(
        self,
        text: str,
        model: str,
        model_name: str,
        chunk_size: int = 5000,
        overlap: int = 1000,
    ) -> tuple:
        """Process a transcript text."""

        try:
            if not text:
                raise ValueError("Empty transcript text provided")

            if chunk_size <= 0:
                raise ValueError("chunk_size must be positive")
            if overlap < 0:
                raise ValueError("overlap must be non-negative")
            if overlap >= chunk_size:
                overlap = chunk_size - 1

            step_size = chunk_size - overlap
            if step_size <= 0:
                chunk_size = overlap + 1

            logger.info(
                f"Processing transcript of length {len(text)} with chunk_size={chunk_size}, overlap={overlap}"
            )
            num_chunks, all_json_data = await self.transcript_processor.process_transcript(
                text=text,
                model=model,
                model_name=model_name,
                chunk_size=chunk_size,
                overlap=overlap,
            )
            logger.info(f"Successfully processed transcript into {num_chunks} chunks")

            return num_chunks, all_json_data
        except Exception as e:  # pragma: no cover - log and re-raise
            logger.error(f"Error processing transcript: {str(e)}", exc_info=True)
            raise

    def cleanup(self) -> None:
        """Cleanup resources."""

        try:
            logger.info("Cleaning up resources")
            if hasattr(self, "transcript_processor"):
                self.transcript_processor.cleanup()
            logger.info("Cleanup completed successfully")
        except Exception as e:  # pragma: no cover - log errors during cleanup
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)


processor = SummaryProcessor()


@router.get("/get-meetings", response_model=List[MeetingResponse])
async def get_meetings(current_user: User = Depends(get_current_active_user)):
    """Get all meetings with their basic information."""

    try:
        meetings = await processor.db.get_all_meetings()
        return [{"id": meeting["id"], "title": meeting["title"]} for meeting in meetings]
    except Exception as e:
        logger.error(f"Error getting meetings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings/{meeting_id}", response_model=MeetingDetailsResponse)
async def get_meeting(meeting_id: str):
    """Get a specific meeting by ID with all its details."""

    try:
        meeting = await processor.db.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/{meeting_id}/title")
async def save_meeting_title(meeting_id: str, data: MeetingTitleUpdate):
    """Save a meeting title."""

    try:
        await processor.db.update_meeting_title(meeting_id, data.title)
        return {"message": "Meeting title saved successfully"}
    except Exception as e:
        logger.error(f"Error saving meeting title: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_active_admin),
):
    """Delete a meeting and all its associated data."""

    try:
        success = await processor.db.delete_meeting(meeting_id)
        if success:
            return {"message": "Meeting deleted successfully"}
        raise HTTPException(status_code=500, detail="Failed to delete meeting")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def process_transcript_background(
    process_id: str, transcript: TranscriptRequest, meeting_id: str | None = None
):
    """Background task to process transcript."""

    if meeting_id is None:
        meeting_id = process_id

    try:
        logger.info(f"Starting background processing for process_id: {process_id}")

        num_chunks, all_json_data = await processor.process_transcript(
            text=transcript.text,
            model=transcript.model,
            model_name=transcript.model_name,
            chunk_size=transcript.chunk_size,
            overlap=transcript.overlap,
        )

        final_summary = {
            "MeetingName": "",
            "SectionSummary": {"title": "Section Summary", "blocks": []},
            "CriticalDeadlines": {"title": "Critical Deadlines", "blocks": []},
            "KeyItemsDecisions": {"title": "Key Items & Decisions", "blocks": []},
            "ImmediateActionItems": {"title": "Immediate Action Items", "blocks": []},
            "NextSteps": {"title": "Next Steps", "blocks": []},
            "OtherImportantPoints": {
                "title": "Other Important Points",
                "blocks": [],
            },
            "ClosingRemarks": {"title": "Closing Remarks", "blocks": []},
        }

        for json_str in all_json_data:
            try:
                json_dict = json.loads(json_str)
                if "MeetingName" in json_dict and json_dict["MeetingName"]:
                    final_summary["MeetingName"] = json_dict["MeetingName"]
                for key in final_summary:
                    if (
                        key != "MeetingName"
                        and key in json_dict
                        and isinstance(json_dict[key], dict)
                        and "blocks" in json_dict[key]
                        and isinstance(json_dict[key]["blocks"], list)
                    ):
                        final_summary[key]["blocks"].extend(json_dict[key]["blocks"])
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON chunk for {process_id}: {e}. Chunk: {json_str[:100]}..."
                )
            except Exception as e:
                logger.error(
                    f"Error processing chunk data for {process_id}: {e}. Chunk: {json_str[:100]}..."
                )

        if final_summary["MeetingName"]:
            await processor.db.update_meeting_name(meeting_id, final_summary["MeetingName"])

        if all_json_data:
            await processor.db.update_process(
                process_id, status="completed", result=json.dumps(final_summary)
            )
            logger.info(f"Background processing completed for process_id: {process_id}")
        else:
            error_msg = (
                "Summary generation failed: No summary could be generated. Please check your model/API key settings."
            )
            await processor.db.update_process(process_id, status="failed", error=error_msg)
            logger.error(
                f"Background processing failed for process_id: {process_id} - {error_msg}"
            )

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Error in background processing for {process_id}: {error_msg}", exc_info=True
        )
        try:
            await processor.db.update_process(
                process_id, status="failed", error=error_msg
            )
        except Exception as db_e:  # pragma: no cover - error during error handling
            logger.error(
                f"Failed to update DB status to failed for {process_id}: {db_e}", exc_info=True
            )


@router.post("/meetings/{meeting_id}/summary")
async def process_transcript_api(
    meeting_id: str, transcript: TranscriptRequest, background_tasks: BackgroundTasks
):
    """Process a transcript text with background processing."""

    try:
        process_id = await processor.db.create_process(meeting_id)

        await processor.db.save_transcript(
            meeting_id,
            transcript.text,
            transcript.model,
            transcript.model_name,
            transcript.chunk_size,
            transcript.overlap,
        )

        background_tasks.add_task(
            process_transcript_background, process_id, transcript, meeting_id=meeting_id
        )

        return JSONResponse({"message": "Processing started", "process_id": process_id})
    except Exception as e:
        logger.error(f"Error in process_transcript_api: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings/{meeting_id}/summary")
async def get_summary(meeting_id: str):
    """Get the summary for a given meeting ID."""

    try:
        result = await processor.db.get_transcript_data(meeting_id)
        if not result:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "meetingName": None,
                    "meeting_id": meeting_id,
                    "data": None,
                    "start": None,
                    "end": None,
                    "error": "Meeting ID not found",
                },
            )

        status = result.get("status", "unknown").lower()

        summary_data = None
        if result.get("result"):
            try:
                parsed_result = json.loads(result["result"])
                if isinstance(parsed_result, str):
                    summary_data = json.loads(parsed_result)
                else:
                    summary_data = parsed_result
                if not isinstance(summary_data, dict):
                    logger.error(
                        f"Parsed summary data is not a dictionary for meeting {meeting_id}"
                    )
                    summary_data = None
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON data for meeting {meeting_id}: {str(e)}"
                )
                status = "failed"
                result["error"] = f"Invalid summary data format: {str(e)}"
            except Exception as e:
                logger.error(
                    f"Unexpected error parsing summary data for {meeting_id}: {str(e)}"
                )
                status = "failed"
                result["error"] = f"Error processing summary data: {str(e)}"

        response = {
            "status": "processing"
            if status in ["processing", "pending", "started"]
            else status,
            "meetingName": summary_data.get("MeetingName")
            if isinstance(summary_data, dict)
            else None,
            "meeting_id": meeting_id,
            "start": result.get("start_time"),
            "end": result.get("end_time"),
            "error": result.get("error"),
            "data": summary_data,
        }

        if status == "failed":
            response["data"] = None
            response["meetingName"] = None
            return JSONResponse(status_code=400, content=response)
        elif status in ["processing", "pending", "started"]:
            response["data"] = None
            return JSONResponse(status_code=202, content=response)
        elif status == "completed":
            if not summary_data:
                response["status"] = "error"
                response["error"] = "Completed but summary data is missing or invalid"
                response["data"] = None
                response["meetingName"] = None
                return JSONResponse(status_code=500, content=response)
            return JSONResponse(status_code=200, content=response)
        else:
            response["status"] = "error"
            response["error"] = f"Unknown or unexpected status: {status}"
            response["data"] = None
            response["meetingName"] = None
            return JSONResponse(status_code=500, content=response)
    except Exception as e:
        logger.error(
            f"Error getting summary for {meeting_id}: {str(e)}", exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "meetingName": None,
                "meeting_id": meeting_id,
                "data": None,
                "start": None,
                "end": None,
                "error": f"Internal server error: {str(e)}",
            },
        )


@router.post("/meetings")
async def create_meeting(request: SaveTranscriptRequest):
    """Create a meeting and save transcript segments without processing."""

    try:
        logger.info(
            f"Received save-transcript request for meeting: {request.meeting_title}"
        )
        logger.info(f"Number of transcripts to save: {len(request.transcripts)}")

        meeting_id = f"meeting-{int(time.time() * 1000)}"
        await processor.db.save_meeting(meeting_id, request.meeting_title)

        for transcript in request.transcripts:
            await processor.db.save_meeting_transcript(
                meeting_id=meeting_id,
                transcript=transcript.text,
                timestamp=transcript.timestamp,
                summary="",
                action_items="",
                key_points="",
            )

        logger.info("Transcripts saved successfully")
        return {
            "status": "success",
            "message": "Transcript saved successfully",
            "meeting_id": meeting_id,
        }
    except Exception as e:
        logger.error(f"Error saving transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-meeting-title")
async def save_meeting_title_legacy(data: MeetingTitleRequest):
    return await save_meeting_title(data.meeting_id, data)


@router.post("/delete-meeting")
async def delete_meeting_legacy(
    data: DeleteMeetingRequest,
    current_user: User = Depends(get_current_active_admin),
):
    return await delete_meeting(data.meeting_id, current_user)


@router.post("/process-transcript")
async def process_transcript_endpoint(
    request: ProcessTranscriptRequest, background_tasks: BackgroundTasks
):
    return await process_transcript_api(request.meeting_id, request, background_tasks)


@router.get("/get-summary/{meeting_id}")
async def get_summary_legacy(meeting_id: str):
    return await get_summary(meeting_id)


__all__ = ["router", "processor", "process_transcript_background"]

