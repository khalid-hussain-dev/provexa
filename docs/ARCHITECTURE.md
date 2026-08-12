# PROVEXA — Architecture

## 1. Architectural principle

PROVEXA is organized around a central **Candidate Capability Model**.

The architecture separates:

1. Experience
2. Platform
3. Intelligence & integrations
4. Persistent data and transient state

AI is used where reasoning adds value. Deterministic software is used for validation, storage, routing, scoring infrastructure, and external API access.

## 2. High-level architecture

```text
                         ┌──────────────────┐
                         │      USER        │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │ EXPERIENCE LAYER │
                         │ Web application  │
                         └────────┬─────────┘
                                  │
                            REST / WS
                                  │
                         ┌────────▼─────────┐
                         │   FASTAPI API    │
                         │  PLATFORM LAYER  │
                         └────────┬─────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
       Candidate Domain      Opportunity Domain   Assessment Domain
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                         ┌────────▼─────────┐
                         │ CAPABILITY ENGINE│
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │    CrewAI        │
                         │ AI Orchestration  │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │   LLM GATEWAY    │
                         └────────┬─────────┘
                                  │
                   ┌──────────────┼──────────────┐
                   ▼              ▼              ▼
                 Groq          Gemini       NVIDIA NIM

        ┌──────────────────┐        ┌──────────────────┐
        │   PostgreSQL     │        │      Redis       │
        │ Persistent truth │        │ Cache / sessions │
        └──────────────────┘        └──────────────────┘

             External integrations:
             GitHub / Job Providers / Other APIs
```

## 3. Modular monolith

The backend should remain a modular monolith for the hackathon.

Do not split every feature into separately deployed microservices.

Benefits:

- Faster development
- Easier local setup
- Easier integration
- Fewer deployment failure points
- Clear internal boundaries without operational overhead

## 4. Module boundaries

### Experience Layer
Owns user interface and API client behavior.

### Platform Layer
Owns authentication, persistence, domain APIs, validation, Redis, and database access.

### Intelligence Layer
Owns CrewAI, AI tasks, prompts, LLM gateway, AI validators, GitHub analysis, job-provider adapters, and recommendation logic.

### Integration Layer
Owns the final connection between modules and end-to-end validation.

## 5. Dependency rule

Modules may depend on **contracts**, not on another module's internal implementation.

Example:

```text
Frontend
   ↓
API Contract
   ↓
Backend implementation
```

The frontend must not import backend internals.

## 6. AI boundary

AI output must pass through:

```text
LLM
 ↓
Structured output
 ↓
Schema validation
 ↓
Business validation
 ↓
Persistence / response
```

The LLM must not directly mutate the database.

## 7. Failure philosophy

No single external provider should be capable of destroying the demo.

Use:

- Provider adapters
- LLM fallbacks
- Redis caching
- Seeded job data
- Mock integration fallback where necessary

## 8. Integration principle

During parallel development, modules remain isolated.

After module freeze:

```text
Experience + Platform + Intelligence
                ↓
          Integration Lead
                ↓
        End-to-end system
```

The Integration Lead should integrate first and redesign only when necessary.
