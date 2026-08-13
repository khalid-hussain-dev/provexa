# AuthKit (Batch 1 core)

Standalone, framework-independent authentication core extracted from the PROVEXA project.

Batch 1 delivers:

- Core domain types (AuthUser, TokenPair, SessionPayload, TwoFactorSetup).
- AuthKitConfig for runtime configuration.
- Password hashing and verification (PBKDF2, PROVEXA-compatible).
- JWT creation/decoding/expiry/purpose validation.
- UserRepository and SessionStore protocols.
- Redis-backed and explicit test-only in-memory session stores.
- AuthService core behavior (signup, authenticate, password reset, 2FA helpers).

## Development

Install in editable mode with dev dependencies:

```bash
cd gigs/authkit
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
pip install -e .[dev]
```

Run the Batch 1 unit tests:

```bash
pytest tests
```

Importability check (must succeed with only stdlib available):

```bash
python -c "import authkit; print(authkit.__version__)"
```

FastAPI and PROVEXA adapters are implemented in later batches and are intentionally out of scope here.
