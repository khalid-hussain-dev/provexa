# PROVEXA — Integration Guide

## 1. Goal

Combine the independently developed Experience, Platform, and Intelligence modules into one runnable product without unnecessary rewrites.

## 2. Before integration

Verify:

- All modules build/start independently.
- API contracts are implemented or mocked.
- Environment variables are documented.
- No secrets are committed.
- Module ownership boundaries were respected.
- Shared models are consistent.

## 3. Integration order

Recommended order:

```text
1. Infrastructure
   PostgreSQL + Redis

2. Platform
   FastAPI + auth + database

3. Intelligence
   AI gateway + CrewAI + integrations

4. Experience
   Frontend connected to real API

5. End-to-end flow
   Candidate → Job → Analysis → Interview → Course → Resume
```

## 4. Replace mocks gradually

Do not replace every mock at once.

Recommended:

```text
Frontend mock
   ↓
Authentication API
   ↓
Candidate API
   ↓
Analysis API
   ↓
Job API
   ↓
Interview API
   ↓
Course API
   ↓
Resume API
```

## 5. Integration Lead rules

- Preserve working module behavior.
- Fix contract mismatches at the correct boundary.
- Avoid unnecessary refactoring.
- Record significant integration decisions.
- Test after each major connection.
- Keep a known-good commit/tag before risky changes.

## 6. Demo fallback

The golden demo must remain operational if:

- A job provider fails.
- GitHub is unavailable.
- An LLM provider rate-limits.
- A generated resource takes too long.

Use cached or seeded data where appropriate.

## 7. Final integration target

The final application should support one coherent path:

```text
Login
 ↓
Candidate Evidence
 ↓
Target Job
 ↓
Analysis
 ↓
Readiness
 ↓
Interview
 ↓
Verdict
 ↓
Learning Path
 ↓
Tailored Resume
```
