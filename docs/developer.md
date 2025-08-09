# Developer Guide

This guide outlines how to set up the project for local development and run tests.

## Local Setup
1. **Install dependencies**
   - Node.js 18+
   - Python 3.10+
   - FFmpeg
   - Rust toolchain (for optional audio processing features)
2. **Clone the repository**
```bash
git clone https://github.com/Zackriya-Solutions/meeting-minutes.git
cd meeting-minutes
```
3. **Install Python packages**
```bash
pip install -r backend/requirements.txt
```
4. **Install frontend packages**
```bash
cd frontend
npm install
cd ..
```

## Environment Variables
Create a `.env` file in `backend/` with values appropriate for your environment:

```
ALLOWED_ORIGINS=http://localhost:3000
SECRET_KEY=change-me
```
Additional variables may be referenced in the code; inspect `backend/app/config.py` for more options.

## Running the Backend
```bash
cd backend
python app/main.py
```
The API will be available at `http://localhost:5167` by default.

## Running the Frontend
```bash
cd frontend
npm run dev
```
The app will be available at `http://localhost:3000`.

## Testing
Run the available test suites before submitting changes:
```bash
# Backend tests
pytest backend/tests

# Service tests
pytest services/tests

# Integration tests (if present)
pytest tests/integration/
```
