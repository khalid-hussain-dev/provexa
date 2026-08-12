# PROVEXA — Environment

## Runtime

The exact versions should be frozen before implementation. Recommended baseline:

```text
Python 3.12+
Node.js 20+
PostgreSQL 16+
Redis 7+
```

## Required environment categories

```text
DATABASE_URL=
REDIS_URL=

JWT_SECRET=
SESSION_SECRET=

GROQ_API_KEY=
GEMINI_API_KEY=
NVIDIA_API_KEY=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

JOB_PROVIDER_API_KEY=
```

Only variables required by the final implementation should remain in `.env.example`.

## Rules

- Never commit `.env`.
- Never place API keys in frontend source.
- Never expose provider keys to browser code.
- Use `.env.example` for documentation.
- Use Docker Compose for local PostgreSQL/Redis where practical.

## Local services

Recommended:

```text
Frontend
Backend
PostgreSQL
Redis
```

The final repository should provide a simple local startup path.
