# PROVEXA — Integration Lead Task

## Role

You are the **Integration Lead**.

Your job begins after the Experience, Platform, and Intelligence modules have reached a stable milestone.

## Read first

Read all project documentation, especially:

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `API_CONTRACTS.md`
- `DATA_MODELS.md`
- `INTEGRATION_GUIDE.md`
- `INTEGRATION_CHECKLIST.md`
- `ARCHITECTURE_DECISIONS.md`
- all three builder task files

## Mission

Integrate the independently developed modules into one reliable, demonstrable PROVEXA system.

## Rules

1. Do not redesign functioning modules without a clear reason.
2. Preserve API contracts where possible.
3. Fix mismatches at the correct boundary.
4. Never delete working functionality merely to simplify integration.
5. Keep a known-good checkpoint before risky changes.
6. Test after every major integration step.
7. Document significant architectural changes.

## Integration order

```text
Infrastructure
 ↓
Platform
 ↓
Intelligence
 ↓
Experience
 ↓
Golden Path
```

## Golden Path

```text
Login
 ↓
Candidate Evidence
 ↓
Target Job
 ↓
Candidate/Job Analysis
 ↓
Readiness
 ↓
Job-Specific Interview
 ↓
Interview Verdict
 ↓
Personalized Learning Path
 ↓
Tailored Resume
```

## Final objectives

- Full system starts reliably.
- Major API contracts connect.
- Authentication works.
- AI workflows work.
- External integrations have fallbacks.
- Redis/PostgreSQL operate correctly.
- Code Gigs are demonstrable.
- Golden demo path is stable.
- UI is polished enough for judging.
- README and documentation are complete.
