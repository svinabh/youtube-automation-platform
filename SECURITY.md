# Security
Never commit secrets. Publishing is disabled by default and refuses unless the artifact is human-approved, rights-cleared and policy-passed. Production requires TLS, secret management, OAuth token protection, least privilege, backups, durable audit retention and rate limiting.

CORS: production must explicitly set `ALLOWED_ORIGINS` to the exact trusted frontend origins. The wildcard `*` is prohibited; do not deploy with permissive cross-origin access.
