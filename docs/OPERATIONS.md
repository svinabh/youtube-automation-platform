# Operations

One-time: install Docker, copy .env.example to .env, run docker compose up --build, open http://localhost:3000. Configure Ollama for local generation. Configure Google OAuth only after staging.

Daily: dashboard -> pending approvals -> inspect evidence -> approve/reject.

Emergency: set GLOBAL_KILL_SWITCH=true and restart backend.

Before real uploads: managed Postgres, TLS, secret manager, OAuth token encryption/refresh, resumable upload, durable logs, backups and staging E2E tests.
