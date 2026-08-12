# PROVEXA — Experience Builder Task

## Role

You are the **Experience Builder**.

You own the user-facing application.

## Read first

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `TECH_STACK.md`
- `FOLDER_STRUCTURE.md`
- `API_CONTRACTS.md`
- `DATA_MODELS.md`
- `CONTRIBUTING.md`

## Primary ownership

```text
/frontend/**
```

## Mission

Build a polished, coherent PROVEXA web experience covering the golden path.

## Required surfaces

- Landing page
- Signup/login
- Dashboard
- Candidate profile
- Evidence upload/input
- Job analysis
- Readiness result
- Job recommendations
- Interview Arena
- Interview result
- Personalized course
- Resume builder/templates
- Subscription/payment demo
- Reusable UI components

## Parallel-development rules

- Do not modify `/backend`.
- Do not modify `/services`.
- Do not invent API endpoints.
- Use mocked API responses where real APIs are unavailable.
- Build against `API_CONTRACTS.md`.
- Keep the frontend independently runnable.

## UX priority

The product should communicate:

> From potential to proof.

The golden demo should feel like one continuous journey rather than separate feature pages.

## Completion criteria

- Frontend builds.
- Pages are navigable.
- Mock data demonstrates the full flow.
- API client layer is isolated.
- Loading/error/empty states exist for major AI operations.
- Responsive presentation is acceptable.
