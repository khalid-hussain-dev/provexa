# PROVEXA — Platform Builder Task

## Role

You are the **Platform Builder**.

You own the backend platform, persistence, authentication, and core APIs.

## Read first

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `TECH_STACK.md`
- `FOLDER_STRUCTURE.md`
- `API_CONTRACTS.md`
- `DATA_MODELS.md`
- `ENVIRONMENT.md`
- `CONTRIBUTING.md`

## Primary ownership

```text
/backend/**
```

## Mission

Build a clean FastAPI modular backend implementing the shared contracts.

## Responsibilities

- FastAPI application
- Authentication
- Signup/login
- Forgot password demo/flow
- 2FA
- Candidate management
- Evidence management
- PostgreSQL integration
- Redis integration
- Core domain APIs
- Validation
- Error handling
- CORS/configuration
- Basic security controls

## Rules

- Do not implement AI logic inside random endpoints.
- Call AI functionality through defined service boundaries.
- Do not modify `/frontend`.
- Do not modify `/services` except where an explicit interface requires coordination.
- Follow API contracts.
- Keep database access isolated.
- Use migrations/schema management appropriate to the chosen stack.

## Completion criteria

- Backend starts independently.
- Database initializes/connects.
- Redis connects.
- Auth works.
- Contract endpoints exist.
- Mock/stub AI responses can be returned where Intelligence Builder is not yet integrated.
- API documentation is available through FastAPI/OpenAPI.
