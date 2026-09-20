# Architecture

FastAPI is the control plane and PostgreSQL is durable state. Redis is intentionally not deployed until a real worker/queue is implemented; unused infrastructure is not presented as active architecture.

Lifecycle:
IDEA -> RESEARCHED -> SCRIPTED -> GENERATED -> QC -> POLICY -> READY_FOR_REVIEW -> APPROVED -> UPLOADED.

SCRIPTED calls the configured AI provider; Ollama is the default. A variation guard compares each new script with the previous 10 stored scripts before GENERATED.

GENERATED invokes a real FFmpeg renderer and stores an MP4 artifact. Current renderer output is a one-second silent MP4; final TTS/scene/caption assembly is still pending.

Advertiser pre-check now returns LOW/MEDIUM/HIGH. HIGH blocks policy progression; MEDIUM is flagged for review; LOW is clear. This is a conservative heuristic, not a guarantee of monetization.

YouTube publishing remains behind a publisher adapter and is disabled until OAuth/resumable-upload staging tests pass.
