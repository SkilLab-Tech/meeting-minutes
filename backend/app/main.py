"""Application entry point for the FastAPI backend."""

import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from auth import router as auth_router
from db import DatabaseManager
from routers import meetings
from schemas.meetings import AsyncSummaryRequest, SaveModelConfigRequest, TranscriptRequest
from tasks import generate_summary_task


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d - %(funcName)s()] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(console_handler)

app = FastAPI(
    title="Meeting Summarizer API",
    description="API for processing and summarizing meeting transcripts",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Cache-Control", "Pragma", "Expires"],
    max_age=3600,
)

db = DatabaseManager()

app.include_router(auth_router)
app.include_router(meetings.router)

# Expose processor for backwards compatibility with tests
processor = meetings.processor
process_transcript_background = meetings.process_transcript_background
async_summary_results: dict[str, dict] = {}


@app.get("/model-config")
async def get_model_config():
    """Get the current model configuration."""

    model_config = await db.get_model_config()
    api_key = await db.get_api_key(model_config["provider"])
    if api_key is not None:
        model_config["apiKey"] = api_key
    return model_config


@app.post("/model-config")
async def save_model_config(request: SaveModelConfigRequest):
    """Save the model configuration."""

    await db.save_model_config(request.provider, request.model, request.whisperModel)
    if request.apiKey is not None:
        await db.save_api_key(request.apiKey, request.provider)
    return {"status": "success", "message": "Model configuration saved successfully"}


@app.get("/api-key/{provider}")
async def get_api_key(provider: str):
    """Get the API key for a given provider."""

    return await db.get_api_key(provider)


@app.post("/summary/async")
async def create_async_summary(request: AsyncSummaryRequest):
    """Create an asynchronous summary task."""

    task = generate_summary_task.apply(args=(request.text,))
    async_summary_results[task.id] = task.result
    return {"task_id": task.id}


@app.get("/summary/async/{task_id}")
async def get_async_summary(task_id: str):
    """Fetch the result of an asynchronous summary task."""
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true":
        if task_id in async_summary_results:
            return {"status": "completed", "result": async_summary_results[task_id]}
        return {"status": "processing"}
    result = generate_summary_task.AsyncResult(task_id)
    if result.ready():
        return {"status": "completed", "result": result.result}
    return {"status": "processing"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on API shutdown."""

    logger.info("API shutting down, cleaning up resources")
    try:
        meetings.processor.cleanup()
        logger.info("Successfully cleaned up resources")
    except Exception as e:  # pragma: no cover - best effort cleanup
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=5167)

