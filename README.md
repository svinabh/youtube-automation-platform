# YouTube Automation Platform

An AI-Powered YouTube Content & Growth Operating System. This repository houses a modular monolith utilizing FastAPI for the backend, Next.js for the frontend, and a Celery/Redis stack for complex background media orchestration.

## Current Status
**Phase 1: Foundation** - Basic backend routing, frontend boilerplate, Docker compose networking, and CI pipelines have been established.

## Repository Structure
- `backend/`: FastAPI Python application.
- `frontend/`: Next.js React frontend.
- `.github/workflows/`: CI/CD pipelines.

## Prerequisites
- Docker & Docker Compose
- Node.js (v22+)
- Python (3.12+)

## Local Backend Setup
1. Navigate to the `backend/` directory.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate the environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests (from the root directory): `export PYTHONPATH=$(pwd) && pytest backend/tests/test_health.py`

## Local Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Docker Setup
A complete development environment is provided via Docker Compose.
1. Copy `.env.example` to `.env` (fill in any required variables).
2. Run `docker compose up --build`
3. The backend will be available at `http://localhost:8000`
4. The frontend will be available at `http://localhost:3000`

## API Health Endpoint
You can verify the backend is running properly by hitting the health check endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

## Development Notes
Please adhere strictly to the rules defined in `ARCHITECTURE.md`. Do not implement business logic for future phases without prior architectural approval.
