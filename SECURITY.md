# Security
Never commit secrets. Publishing is disabled by default and refuses unless the artifact is human-approved, rights-cleared and policy-passed. Production requires TLS, secret management, OAuth token protection, least privilege, backups, durable audit retention and rate limiting.

## CORS
Set `ALLOWED_ORIGINS` explicitly in production to the exact trusted frontend origin(s). The wildcard `*` is not permitted as a production configuration.
