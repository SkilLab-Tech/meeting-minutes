# API Documentation

This document outlines the REST endpoints exposed by the Meeting Summarizer backend. All endpoints are served from the FastAPI application defined in `backend/app/main.py`.

## Authentication

### `POST /token`
- **Description:** Obtain an access and refresh token.
- **Auth:** None
- **Sample request:**
```bash
curl -X POST http://localhost:5167/token \
  -d "username=alice&password=secret"
```
- **Sample response:**
```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer"
}
```

### `POST /refresh`
- **Description:** Exchange a refresh token for a new access token.
- **Auth:** None
- **Sample request:**
```bash
curl -X POST http://localhost:5167/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<JWT>"}'
```
- **Sample response:** same as `/token`.

## Meetings

### `GET /get-meetings`
- **Description:** List all meetings.
- **Auth:** Bearer token required.
- **Sample response:**
```json
[
  {"id": "meeting-1", "title": "Sprint Planning"}
]
```

### `GET /meetings/{meeting_id}`
- **Description:** Retrieve details for a single meeting.
- **Auth:** None.
- **Sample response:**
```json
{
  "id": "meeting-1",
  "title": "Sprint Planning",
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2024-12-01T10:30:00Z",
  "transcripts": []
}
```

### `POST /meetings`
- **Description:** Create a meeting and upload transcript segments without processing.
- **Auth:** None.
- **Sample request:**
```bash
curl -X POST http://localhost:5167/meetings \
  -H "Content-Type: application/json" \
  -d '{"meeting_title":"Demo","transcripts":[]}'
```

### `POST /meetings/{meeting_id}/summary`
- **Description:** Start background transcript processing for a meeting.
- **Auth:** None.
- **Sample request:**
```bash
curl -X POST http://localhost:5167/meetings/meeting-1/summary \
  -H "Content-Type: application/json" \
  -d '{"text":"...","model":"gpt","model_name":"gpt-4"}'
```
- **Sample response:**
```json
{"message": "Processing started", "process_id": "process-123"}
```

### `GET /meetings/{meeting_id}/summary`
- **Description:** Retrieve processing status or final summary for a meeting.
- **Auth:** None.

### `POST /meetings/{meeting_id}/title`
- **Description:** Update the title of a meeting.
- **Auth:** None.

### `DELETE /meetings/{meeting_id}`
- **Description:** Delete a meeting and associated data.
- **Auth:** None.

Administrative variants `/save-meeting-title` and `/delete-meeting` require an admin token.

## Model Configuration

### `GET /model-config`
- **Description:** Return the current model configuration.
- **Auth:** None.

### `POST /model-config`
- **Description:** Persist a new model configuration and optional API key.
- **Auth:** None.

### `GET /api-key/{provider}`
- **Description:** Fetch a stored API key for a provider.
- **Auth:** None.

## Asynchronous Summaries

### `POST /summary/async`
- **Description:** Queue an asynchronous summary task.
- **Auth:** None.
- **Sample response:**
```json
{"task_id": "celery-task-id"}
```

### `GET /summary/async/{task_id}`
- **Description:** Poll an asynchronous summary task for completion.
- **Auth:** None.

## OpenAPI
FastAPI automatically exposes an OpenAPI specification at `/openapi.json` and an interactive Swagger UI at `/docs` when the server is running.
