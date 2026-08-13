# Configuration

`AuthKitConfig.jwt_secret_key` is required. Production-like environments must
provide `redis_url`; memory sessions are rejected unless the environment is
development/test and the explicit flag is enabled.

Never log secrets, tokens, reset tokens, TOTP secrets, or Redis URLs.
