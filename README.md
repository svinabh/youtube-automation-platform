# YouTube Automation Platform

Verified pipeline: AI script generation -> variation guard -> real FFmpeg MP4 render -> QC/policy -> human review.

The current FFmpeg output is a real one-second silent MP4, not the final TTS/visual/caption production pipeline.

Human approval is ON by default and publishing is OFF by default. Daily founder workflow: dashboard -> pending approvals -> inspect evidence -> approve/reject.

For local development, the default `ALLOWED_ORIGINS` is `["http://localhost:3000"]`. Production deployments must explicitly set `ALLOWED_ORIGINS` to the exact trusted frontend origins; never use `*` as an origin.
