# ARCHITECTURE

This document outlines the architectural principles for the AI-Powered YouTube Content & Growth Operating System. The application is built as a **Modular Monolith** and enforces strict boundaries across its various implementation phases.

## 1. Product Purpose
The platform acts as a complete operating system for YouTube automation—managing everything from topic discovery and script generation to rendering, human approval, and analytics insights. It is explicitly not a simple uploader; it is an intelligent pipeline.

## 2. High-Level Architecture
- **Backend**: FastAPI (Python), providing a robust, type-safe API using Pydantic and orchestrated background tasks.
- **Frontend**: Next.js (React + TypeScript), structured for eventual workflow-oriented dashboards.
- **Database**: PostgreSQL (relational state, content tracking, and metrics).
- **Background Jobs**: Celery backed by Redis, essential for idempotency, retry mechanisms, and managing long-running AI or media generation tasks.
- **Infrastructure**: Docker and Docker Compose for a reproducible local development environment.

## 3. Backend/Frontend Separation
- The backend serves entirely as a stateless API layer and task orchestrator. It does not render HTML.
- The frontend acts as an independent Next.js application consuming the FastAPI endpoints.

## 4. Modular Monolith Approach
We begin with a single backend repository housing distinct logical modules (e.g., `auth`, `content_intelligence`, `media_pipeline`). This avoids the unnecessary complexity of microservices while preserving the ability to split services in the future if a specific module requires independent scaling.

## 5. Provider Abstraction Principle
The application **must not** be hardcoded to single AI or media providers. All external generations—such as Text, TTS, Image, and Video—must happen through defined interfaces (e.g., `TextGenerationProvider`). This allows for safe swapping, mock implementations for testing, and avoiding vendor lock-in.

## 6. API Versioning
All endpoints must be strictly versioned under `/api/v1/`. Changes breaking this contract require bumping the API version.

## 7. Configuration Strategy
Secrets must never be committed. The platform uses a central `.env` file for local development and leverages environment variables exclusively for deployment configuration. See `.env.example` for the expected schema.

## 8. Security Principles
- OAuth flows, API keys, and sensitive database configurations are managed strictly via environment variables.
- The platform enforces ownership boundaries (User A cannot access User B's resources).
- JWTs/Cookies will be implemented in Phase 2 for safe, stateless authentication.

## 9. Human Approval Principle
Publishing content is **never fully automatic by default**. There is a strict, explicit boundary requiring human approval before a compiled artifact is pushed to the official YouTube APIs.

## 10. Phase Boundaries
Implementation is split into strictly isolated, incremental phases. Future phase business logic is **never** implemented early.
- **Phase 1**: Foundation (Current Phase) - Establishes basic routing, CI, and Docker services.
- **Phase 2**: Database + Core APIs - Introduces SQLAlchemy, Alembic, and Auth.
- **Phase 3**: Content Intelligence - Implements topic discovery.
- **Phase 4**: SEO + Packaging Intelligence - Title generation and thumbnail scoring.
- **Phase 5**: AI/TTS/Media Pipeline - Implements provider abstractions.
- **Phase 6**: Video Assembly + Rendering - Actual FFmpeg scene rendering.
- **Phase 7**: YouTube OAuth + Official API - Handles Google OAuth integration.
- **Phase 8**: Analytics + Learning Engine - Closes the feedback loop.
- **Phase 9**: Quality Control + Human Approval - Pre-publish checks.
- **Phase 10**: Production Hardening - Scale and security audits.

## 11. Planned Future Modules
Future phases will introduce `Users`, `Channels`, `TopicSignals`, `ResearchBriefs`, `VideoVariants`, and more. None of these models are to be instantiated in Phase 1.

## 12. Development Workflow
Always verify tests, linting, and a successful Docker build locally before requesting a review. Commit messages must be descriptive and scoped strictly to the current active phase.
