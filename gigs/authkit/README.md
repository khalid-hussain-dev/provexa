# AuthKit

AuthKit is a reusable authentication core for Python applications. It provides
PBKDF2 password hashing, signed access tokens, Redis-backed server-side sessions,
explicit local/test memory sessions, password reset primitives, TOTP support,
and optional FastAPI integration.

## Quick start

Install the core package, then add the optional integrations as needed:

```text
pip install -e .[fastapi,redis]
```

Production applications must configure Redis. The in-memory session store is
available only when `environment` is local/test and
`allow_in_memory_sessions=True`.

See `docs/fastapi.md` and `examples/standalone_fastapi/` for integration.

## Compatibility

AuthKit preserves PROVEXA's password hash format and JWT claim contract. The
PROVEXA adapter is opt-in and does not replace existing PROVEXA routes.

OAuth, subscriptions, frontend work, Experience Builder, and AI behavior are
outside AuthKit's scope.
