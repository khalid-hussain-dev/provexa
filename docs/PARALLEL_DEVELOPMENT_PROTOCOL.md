# PROVEXA — Parallel Development Protocol

## Purpose

PROVEXA will be built concurrently using multiple AI coding environments.

The biggest risk is not coding speed. It is **cross-agent interference**.

This protocol keeps the modules independently buildable until integration.

## 1. Four roles

```text
EXPERIENCE BUILDER
        │
        │ API contract
        ▼
PLATFORM BUILDER
        │
        │ service interfaces
        ▼
INTELLIGENCE BUILDER
        │
        ▼
INTEGRATION LEAD
```

This is a responsibility model, not a model/vendor assignment.

Any AI coding tool may perform any role if instructed to follow that role's task file.

## 2. File ownership

| Area | Owner |
|---|---|
| `/frontend/**` | Experience Builder |
| `/backend/**` | Platform Builder |
| `/services/**` | Intelligence Builder |
| `/docs/**` | Shared, but contract changes require coordination |
| Root configuration | Integration Lead unless explicitly delegated |
| `/tests/integration/**` | Integration Lead |

## 3. No-cross-edit rule

While parallel development is active:

> **An agent must not edit another role's owned directory.**

If a dependency is missing, create a mock/interface rather than modifying the other module.

## 4. Contract-first development

All agents work from:

```text
API_CONTRACTS.md
DATA_MODELS.md
ARCHITECTURE.md
```

The contract is the bridge between independently developed modules.

## 5. Mock-first strategy

Example:

```text
Frontend
  ↓
Mock API client
  ↓
Expected API contract
```

can be developed before the backend exists.

Similarly:

```text
Backend
  ↓
Stub intelligence service
  ↓
Expected intelligence interface
```

can be developed before AI services exist.

## 6. Shared interface rule

When a module needs another module:

```text
DEPENDENCY NEEDED
       ↓
Define expected interface
       ↓
Implement local mock/stub
       ↓
Continue independently
       ↓
Integrator swaps mock for real implementation
```

## 7. Git discipline

Use small commits.

Recommended commit style:

```text
feat(ui): add readiness dashboard
feat(auth): add 2fa verification
feat(ai): add interview crew
feat(jobs): add normalized provider adapter
fix(interview): handle empty answer
```

Avoid massive agent commits where possible.

## 8. Integration freeze

Before integration:

- Stop structural changes.
- Tag/checkpoint each module.
- Record known issues.
- Export required environment variables.
- Confirm independent startup.

Suggested checkpoints:

```text
experience-freeze
platform-freeze
intelligence-freeze
```

## 9. Integration sequence

```text
1. Infrastructure
2. Backend startup
3. Authentication
4. Candidate/evidence
5. Intelligence services
6. Job flow
7. Interview flow
8. Course flow
9. Resume flow
10. Frontend live API connection
11. Golden-path test
12. Demo polish
```

## 10. Conflict resolution

When two implementations disagree:

1. Prefer the documented contract.
2. Prefer the smallest change.
3. Avoid rewriting a completed module.
4. Update the documentation if the contract genuinely needs to change.
5. Test immediately.

## 11. Golden path is the priority

The final product must reliably demonstrate:

```text
Login
 → Evidence
 → Job
 → Match
 → Interview
 → Verdict
 → Course
 → Resume
```

A feature that looks impressive in isolation but destabilizes the golden path should be deprioritized.
