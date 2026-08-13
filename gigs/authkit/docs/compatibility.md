# PROVEXA compatibility

AuthKit preserves:

- `pbkdf2_sha256$260000$<salt_hex>$<digest_hex>` password hashes;
- HS256 JWTs with `sub`, `jti`, `iat`, `exp`, and optional `purpose` claims;
- the `2fa_pending` token purpose;
- Redis keys `<prefix>:session:<jti>` and `<prefix>:session-revoked:<jti>`;
- session TTL and revocation behavior.

The adapter is opt-in. Existing PROVEXA authentication routes remain the source
of truth until a separately reviewed migration.
