# YouTube Automation Platform

Verified pipeline: AI script generation -> variation guard -> real FFmpeg MP4 render -> QC/policy -> human review.

The current FFmpeg output is a real one-second silent MP4, not the final TTS/visual/caption production pipeline.

Human approval is ON by default and publishing is OFF by default. Daily founder workflow: dashboard -> pending approvals -> inspect evidence -> approve/reject.

## Local CORS
Development allows `http://localhost:3000` by default through `ALLOWED_ORIGINS`.

For production, set `ALLOWED_ORIGINS` explicitly to the exact frontend origin(s). Never use `*`.
