# PROVEXA Copy-Based Integration Contract and Risk Report

Status: Phase 3 implemented locally; Experience Builder remains out of scope.

## Architectural decision

The Intelligence Builder remains the host application and the source of truth for all existing AI workflows, prompts, CrewAI orchestration, routes, response semantics, and behavior.

The Platform Builder is integrated underneath that host through compatibility adapters and infrastructure services. Platform owns authentication, persistence, validation, authorization, and durable state. Intelligence produces reasoning results; Platform validates and stores results where a compatible mapping exists.

The existing Intelligence application entry point remains `services/main.py`. Its routes must not be replaced, renamed, shadowed, or semantically changed.

Experience Builder is excluded completely.

## Existing host and capabilities

### Intelligence host

- Entry point: `services/main.py`
- FastAPI application: `app`
- Existing route surface: `/`, `/api/v1/profile/analyze`, `/api/v1/interview/questions`, `/api/v1/interview/evaluate`, `/api/v1/jobs/recommend`, `/api/v1/assessment/complete`, `/api/v1/course/generate`, `/api/v1/resume/inject-skills`
- Core orchestration: `InterviewSystem` in `services/interview_system.py`
- AI workflows: profile analysis, question generation, interview evaluation, course generation, resume optimization, and job recommendations

### Platform capabilities

- Entry point: `backend/app/main.py`, via `create_app()`
- Authentication: signup, login, logout, password reset demo, TOTP setup/verification, protected-user lookup
- Persistence: SQLAlchemy models and repositories; SQLite development fallback and PostgreSQL-ready configuration
- Transient state: Redis-backed cache with in-memory fallback
- Validation: Pydantic request/response schemas and centralized error envelopes
- Domain APIs: candidate/evidence, analysis, jobs, interviews, courses, resumes, and subscription demo
- Current AI boundary: `backend/app/services/intelligence/interfaces.py`; currently not wired into the API flows

## Integration contract

1. Existing Intelligence routes and response semantics remain authoritative.
2. Integration code must translate Platform-owned authenticated/domain data into the existing Intelligence input models without editing Intelligence workflow logic.
3. Integration code must validate Intelligence output before any Platform persistence.
4. Raw LLM/CrewAI output must never be persisted directly.
5. Intelligence must not write to Platform persistence directly.
6. Platform fallbacks remain available whenever AI providers, GitHub, Adzuna, or Redis are unavailable.
7. Conflicting `/api/v1` route shapes must not be mounted at the same path.
8. Secrets are environment-only and must never appear in source, logs, manifests, or reports.
9. All integration changes are confined to `E:\PROVEXA\integration-workspace`.

## Current integration boundary map

| Capability | Authoritative behavior | Proposed copy-only integration | Initial status |
|---|---|---|---|
| Authentication | Platform | Internal auth facade around Intelligence-hosted requests | Implemented Phase 1 |
| Candidate/evidence storage | Platform | Platform repositories provide normalized input to adapters | Implemented Phase 1 |
| Candidate AI analysis | Intelligence profile workflow | Adapter maps `CandidateProfile` and persists validated profile context snapshots | Implemented Phase 2 |
| Job analysis | Platform deterministic analysis | Keep Platform behavior; Intelligence has no matching job-analysis workflow | Deferred |
| Candidate/job match | Platform deterministic scoring | Keep Platform behavior until a compatible Intelligence workflow exists | Deferred |
| Interview questions | Intelligence `InterviewSystem.generate_interview_questions` | Adapter translates Platform candidate/job context and persists questions through Platform | Implemented Phase 3 |
| Interview answers | Platform answer persistence | Keep per-answer Platform state; send the complete transcript to Intelligence for final reasoning | Implemented Phase 3 |
| Interview verdict | Intelligence interview evaluation | Validate and persist an allowlisted `InterviewResult` snapshot without inventing dimension scores | Implemented Phase 3 |
| Learning path | Intelligence `generate_targeted_course` | Adapter maps validated `DetailedCourse` and modules to Platform course records; Platform owns progress | Implemented Phase 4 |
| Resume tailoring | Intelligence optimizer | Use only with explicit owned CV source text and evidence references; Platform remains evidence-lock authority | Implemented Phase 4 |
| Job recommendations | Existing Intelligence route and job service | Preserve Intelligence route; do not mount conflicting Platform route at the same path | Planned host policy |
| Job selection and deterministic match | Platform job repository and analysis service | Expose non-conflicting `/api/v1/integration/platform/*` compatibility routes for the golden path | Implemented Phase 5 |
| Health/readiness | Both modules | Add integration health checks without changing existing route behavior | Implemented Phase 1 |
| Provider readiness | Environment configuration | Report configuration-only Gemini/Groq/GitHub/Adzuna state without secret values or live calls | Implemented Phase 6 |
| Experience/UI | Not implemented | No work in this phase | Out of scope |

## Risks requiring controlled handling

- **Source ambiguity:** `E:\PROVEXA\crew-provexa` is a separate Intelligence repository with a dirty working tree. The copy source is the clean combined `.provexa-review` repository; the related repository is recorded in `SOURCE_MANIFEST.json` but is not modified or used for copying.
- **Import-time AI configuration:** `services/config.py` requires `GEMINI_API_KEY`, and `InterviewSystem` initializes CrewAI components eagerly. Adapters must be lazy and must expose an explicit fallback state.
- **Route collision:** Platform and Intelligence both define `/api/v1/jobs/recommend` with incompatible payloads. Platform routes must not be mounted over the Intelligence host route.
- **Security gap:** Existing Intelligence routes are unauthenticated and use permissive CORS. The integration gateway must add Platform authentication around protected use without changing the underlying Intelligence route implementation.
- **Async/sync mismatch:** Intelligence workflows are async while Platform services and SQLAlchemy sessions are synchronous. The bridge must avoid blocking the event loop and must define transaction boundaries.
- **Schema mismatch:** Intelligence models (`CandidateProfile`, `InterviewResult`, `DetailedCourse`, and related models) differ from the shared Platform API/data models. Every crossing needs explicit DTO mapping and validation.
- **Persistence mismatch:** Platform owns durable records. The Intelligence `DATABASE_URL` and `REDIS_URL` settings must not create a second source of truth.
- **Provider failure:** Gemini, Groq, GitHub, and Adzuna can be unavailable. The host must preserve seeded/deterministic fallback behavior and report provider state without leaking credentials.
- **Evidence safety:** Resume and capability outputs must retain evidence references; an AI confidence value must not upgrade verification status by itself.
