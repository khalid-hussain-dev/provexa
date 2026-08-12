# Auth Foundation

This package contains the temporary backend-local authentication foundation.

- `repository.py` defines a swappable repository interface and in-memory store.
- `passwords.py` hashes passwords with PBKDF2-SHA256 using the Python standard library.
- `tokens.py` creates and validates HS256 JWT access tokens without external services.
- `dependencies.py` exposes the current-user dependency for future protected routes.

The in-memory repository is not production persistence and is intended to be replaced by the database foundation batch.
