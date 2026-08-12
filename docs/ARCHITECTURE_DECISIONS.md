# PROVEXA — Architecture Decisions

## ADR-001 — Product architecture

**Decision:** Use a modular monolith for the hackathon.

**Reason:** Faster development and integration while preserving clear internal module boundaries.

## ADR-002 — Core database

**Decision:** PostgreSQL is the preferred persistent database.

**Reason:** The domain is highly relational. JSONB can support flexible AI-generated structures.

## ADR-003 — Redis

**Decision:** Redis handles transient state and caching.

**Reason:** Low-latency sessions, interview state, API caching, and LLM caching are useful to PROVEXA and help conserve free API quotas.

## ADR-004 — AI orchestration

**Decision:** Use CrewAI for reasoning-heavy multi-agent workflows.

**Reason:** The project benefits from explicit candidate, interview, and learning workflows.

## ADR-005 — LLM abstraction

**Decision:** Use a provider-independent LLM gateway.

**Reason:** Free-provider availability and rate limits can change during the hackathon.

## ADR-006 — Evidence-backed generation

**Decision:** Resume generation must prioritize verified candidate evidence.

**Reason:** The product should improve presentation without fabricating qualifications.

## ADR-007 — External provider fallback

**Decision:** External APIs must have fallback or seeded/demo data.

**Reason:** The live demonstration must not depend on external service availability.

## ADR-008 — Parallel development

**Decision:** Development is divided into isolated domains and integrated only after module freeze.

**Reason:** Multiple AI coding agents may modify files continuously; strict ownership reduces conflicts and context contamination.

## ADR-009 — Code Gigs

**Decision:** Candidate-facing reusable capabilities should become the two primary Code Gig candidates: AuthKit and JobFit Intelligence API.

**Reason:** They satisfy the requirement while remaining genuine reusable components of the product.

> Future decisions should be appended rather than rewriting history.
