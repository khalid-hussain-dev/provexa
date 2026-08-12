# PROVEXA — Technology Stack

## Core stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js / React | Web application |
| Backend | Python + FastAPI | API platform |
| Database | PostgreSQL | Persistent source of truth |
| Cache / state | Redis | Sessions, caching, interview state |
| AI orchestration | CrewAI | Multi-agent task orchestration |
| LLM gateway | Custom Python abstraction | Provider routing and fallback |
| AI providers | Groq / Gemini / NVIDIA NIM | LLM inference |
| GitHub | GitHub API | Repository/profile evidence |
| Jobs | Provider adapters | Job discovery |
| Auth | JWT/session architecture + 2FA | Account security |
| Containers | Docker Compose | Local infrastructure |

## Why PostgreSQL

PostgreSQL is preferred for the core system because PROVEXA contains strongly related entities:

```text
User
 → Candidate
 → Evidence
 → Capability
 → Job
 → Requirement
 → Interview
 → Assessment
 → Course
 → Progress
```

Flexible AI-generated structures may use PostgreSQL JSONB where appropriate.

## Why Redis

Redis is used for:

- Sessions
- Interview state
- Job-result caching
- GitHub-result caching
- LLM response caching
- Rate limiting where useful

## Why CrewAI

CrewAI provides an explicit orchestration layer for reasoning-heavy workflows.

It should not replace normal Python services.

Use CrewAI for:

- Candidate analysis
- Job analysis
- Interview generation/evaluation
- Learning-path generation
- Resume tailoring

Use normal Python for:

- Database access
- API calls
- Authentication
- Caching
- Deterministic scoring infrastructure
- Validation

## LLM provider strategy

The exact provider/model assignment is intentionally configurable.

The application must call the LLM gateway rather than hard-coding a provider throughout the codebase.

The gateway should support:

- Task-based routing
- Provider fallback
- Structured output
- Timeouts
- Retry limits
- Caching
- Provider/model observability

## Environment variables

Provider keys, database credentials, GitHub credentials, and other secrets must come from environment variables.

Never commit `.env`.
