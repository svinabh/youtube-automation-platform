# YouTube Automation Platform

Verified pipeline: AI script generation -> variation guard -> structured video brief -> external finished-video ingestion -> QC/policy -> human review.

This engine does not synthesize the finished video. External tools or a human editor create the finished MP4 and upload it through `POST /api/videos/{id}/media`. FFmpeg is retained only for optional thumbnail-frame extraction.

Human approval is ON by default and publishing is OFF by default. Daily founder workflow: dashboard -> pending approvals -> inspect evidence -> approve/reject.

Media uploads are limited by `MAX_MEDIA_UPLOAD_MB` and stored under the Docker named `media_data` volume.

For local development, the default `ALLOWED_ORIGINS` is `["http://localhost:3000"]`. Production deployments must explicitly set `ALLOWED_ORIGINS` to the exact trusted frontend origins; never use `*` as an origin.
