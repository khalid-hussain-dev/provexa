# Integration Point Map

## Host topology

```text
Intelligence FastAPI host (`services/main.py`)
        │ existing routes and AI behavior remain unchanged
        ▼
Integration gateway / adapters
        ├── Platform authentication
        ├── Platform repositories and persistence
        ├── DTO/schema translation
        ├── business validation
        └── provider/fallback state
```

The eventual composed host must preserve the existing Intelligence route paths. Platform routes with incompatible schemas must remain internal or use an explicitly separate compatibility prefix.

## Intelligence application routes

| Route | Existing behavior | Integration treatment |
|---|---|---|
| `GET /` | Intelligence health response | Preserve unchanged |
| `POST /api/v1/profile/analyze` | Profile/resume/GitHub/web analysis | Preserve route unchanged; the Phase 2 adapter is exposed separately at `/api/v1/integration/profile/analyze` |
| `POST /api/v1/interview/questions` | AI question generation | Preserve route; adapter may supply Platform-owned candidate context |
| `POST /api/v1/interview/evaluate` | Batch AI interview evaluation | Preserve route; adapter submits Platform transcript and validates result |
| `POST /api/v1/jobs/recommend` | Intelligence job recommendation service | Preserve as host route; do not collide with Platform route |
| `POST /api/v1/assessment/complete` | End-to-end Intelligence assessment | Preserve behavior; persistence integration is additive and validated |
| `POST /api/v1/course/generate` | Targeted course generation | Preserve route; map result to Platform persistence only after validation |
| `POST /api/v1/resume/inject-skills` | Resume text optimization | Preserve route; evidence lock remains Platform responsibility |

## Platform capability surface

| Platform capability | Current location | Integration role |
|---|---|---|
| FastAPI application factory | `backend/app/main.py` | Infrastructure reference; not the public AI host |
| Auth routes and dependencies | `backend/app/api/v1/auth.py`, `backend/app/auth/*` | Protect integration entry points and establish current user |
| Database session/models | `backend/app/database/*` | Durable source of truth for Platform records |
| Redis/cache abstraction | `backend/app/core/cache.py` | Shared transient state with fallback |
| Pydantic API schemas | `backend/app/*/schemas.py` | Contract and response validation |
| Error handling | `backend/app/core/errors.py`, `exception_handlers.py` | Stable error envelope |
| Candidate/evidence repositories | `backend/app/candidates/*` | Source payloads for Intelligence adapters |
| Analysis persistence | `backend/app/analysis/*` | Store validated capability, job, and match snapshots |
| Interview persistence | `backend/app/interviews/*` | Store questions, answers, and final verdict |
| Course persistence | `backend/app/courses/*` | Store validated modules and progress |
| Resume persistence | `backend/app/resumes/*` | Enforce evidence-backed structured output |
| Jobs persistence and seeded data | `backend/app/jobs/*` | Preserve Platform job source and deterministic fallback |

## Implemented adapter contracts

- `POST /api/v1/integration/profile/analyze`: authenticated Platform candidate/evidence data is mapped to the existing Intelligence `CandidateProfile` shape, passed through the existing profile-preparation workflow, validated at the boundary, and persisted as an integration-owned profile snapshot.
- Raw or unknown Intelligence fields are not persisted. Capability scores are not invented because the existing profile output does not provide evidence-backed scores.

## Remaining proposed adapter contracts

The next implementation phase should introduce adapters in `integration/` without changing the copied Intelligence workflow code:

- `PlatformCandidateAdapter`: Platform candidate/evidence → existing `CandidateProfile` input.
- `IntelligenceProfileAdapter`: profile context → validated capability/evidence payload.
- `IntelligenceInterviewAdapter`: Platform job/profile/questions/answers → existing Intelligence interview methods and validated Platform verdict.
- `IntelligenceCourseAdapter`: Platform gaps/interview result → existing `generate_targeted_course` output and validated course modules.
- `IntelligenceResumeAdapter`: evidence-backed source text/skills → existing optimizer output, subject to Platform evidence validation.
- `PlatformPersistenceGateway`: validated results → SQLAlchemy repositories and transaction boundaries.
- `ProviderHealth/FallbackGateway`: explicit provider status and deterministic fallback selection.

No adapter is wired in this setup phase.
