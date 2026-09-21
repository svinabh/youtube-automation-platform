# YouTube Automation Platform

Verified pipeline: AI script generation -> variation guard -> structured video brief -> external finished-video ingestion -> QC/policy -> human review.

This engine does not synthesize the finished video. External tools or a human editor create the finished MP4 and upload it through `POST /api/videos/{id}/media`. FFmpeg is retained only for optional thumbnail-frame extraction.

Human approval is ON by default and publishing is OFF by default. Daily founder workflow: dashboard -> pending approvals -> inspect evidence -> approve/reject.

Media uploads are limited by `MAX_MEDIA_UPLOAD_MB` and stored under the Docker named `media_data` volume.

For local development, the default `ALLOWED_ORIGINS` is `["http://localhost:3000"]`. Production deployments must explicitly set `ALLOWED_ORIGINS` to the exact trusted frontend origins; never use `*` as an origin.


### Founder review gate

At READY_FOR_REVIEW, the dashboard presents the uploaded MP4, download fallback, script/brief, rights result, advertiser-risk heuristic, and the disclosure suggestion with its reason in one mobile-friendly review card. The disclosure suggestion is only a pre-fill hint; the founder must explicitly select Yes or No and confirm that they watched the full video and it matches the script/brief. Approval stays disabled until the video is playable, the disclosure choice is explicitly confirmed, and the watch-confirmation checkbox is checked.

Automated checks are text/metadata checks only and cannot verify the actual video/audio. The final visual/audio match decision remains human.


### Founder authentication

All dashboard access and state-changing API endpoints require `Authorization: Bearer <FOUNDER_API_KEY>`. The `/health` endpoint remains public. In production, `FOUNDER_API_KEY` must be set or the backend refuses to start. The founder dashboard stores the key only in the browser's localStorage for that device and sends it with authenticated API requests.
