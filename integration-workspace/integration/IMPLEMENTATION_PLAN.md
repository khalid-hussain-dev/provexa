# Copy-Based Integration Implementation Plan

Status: local integration roadmap through Phase 5 completed. Experience Builder is excluded.

## Completed setup phase

1. Used the clean `.provexa-review` repository as the copy source.
2. Recorded source commit/state and file hashes in `SOURCE_MANIFEST.json`.
3. Copied eligible Platform and Intelligence files into the isolated workspace.
4. Excluded repository metadata, `.env*`, secrets, caches, virtual environments, uploads, generated metadata, and other artifacts.
5. Verified every copied file against its source SHA-256.
6. Documented the host, capabilities, environment names, integration contract, risks, and route map.

## Phase 1: adapter skeleton and contract tests

1. Add lazy adapter interfaces under `integration/`.
2. Add DTOs for candidate profile, interview evaluation, course output, resume output, and provider status.
3. Add fake Intelligence implementations for tests only.
4. Add tests proving Platform-owned validation and persistence boundaries.
5. Do not invoke live LLMs or alter copied Intelligence behavior.

## Phase 2: host-safe Platform infrastructure

1. Establish the Intelligence application as the public host.
2. Add Platform authentication and persistence as internal integration services or explicitly separated compatibility routes.
3. Avoid mounting conflicting Platform `/api/v1` routes over existing Intelligence routes.
4. Add health/readiness reporting for database, Redis, and AI-provider availability.

## Phase 2: candidate/profile-analysis connection

Status: completed locally. The existing Intelligence profile route and workflow files remain unchanged. The protected integration route validates and persists only an allowlisted profile snapshot.

1. Connect candidate/evidence payloads to the existing Intelligence profile workflow. Completed.
2. Validate the returned profile context and persist an integration-owned snapshot. Completed.
3. Preserve deterministic fallback when AI configuration or providers are unavailable. Deferred to provider-readiness work.
4. Run candidate analysis and persistence tests before proceeding. Completed with fake providers.

## Phase 3: interview connection

Status: implemented locally. The adapter preserves Intelligence question generation/evaluation semantics, while Platform owns authenticated interview state, transcript persistence, and ownership boundaries.

1. Preserve Platform answer persistence. Completed.
2. Use existing Intelligence question generation with a validated profile snapshot and Platform job context. Completed.
3. Submit complete transcripts to the existing Intelligence evaluator. Completed.
4. Validate and persist the final Intelligence result without inventing dimension scores. Completed.

## Phase 4: course and resume compatibility

Status: implemented locally. Course generation requires a completed Phase 3 evaluation; resume optimization requires explicit owned CV evidence and course-derived skills.

1. Map existing Intelligence course modules into Platform course records. Completed.
2. Keep Platform progress persistence authoritative. Completed.
3. Test resume optimization only with explicit source text and evidence references. Completed with fake providers.
4. Keep Platform evidence lock authoritative; never infer verification from AI output. Completed.

## Phase 5: local golden-path validation

Status: completed locally with fake Intelligence providers. Experience Builder remains excluded.

Run locally in this order:

```text
Platform auth
→ candidate/evidence persistence
→ Intelligence profile analysis
→ Platform job creation/selection
→ Platform match fallback
→ Intelligence interview generation/evaluation
→ Intelligence course generation
→ Platform progress persistence
→ evidence-backed resume output
```

The full Experience/UI flow is intentionally not tested because Experience Builder is not implemented.

The local golden-path test is `tests/integration/test_phase5_golden_path.py`. Platform job selection and deterministic matching use the non-conflicting `/api/v1/integration/platform/*` compatibility routes.

## Release gates

- Original source workspaces remain unchanged.
- Manifest verification passes after every copy/workspace change.
- No secret values are present in files, logs, or reports.
- Existing Intelligence routes return their original shapes and semantics.
- Provider failure leaves a deterministic fallback path.
- Platform persistence contains only validated integration results.
- Backend and Intelligence baseline checks pass independently.
- Integration tests pass with fake providers before any live-key test.

## Next smallest safe implementation batch

Review the completed local golden path and decide whether to publish Phase 5. Any future live-provider verification, production deployment hardening, or Experience Builder work requires a separate explicit scope decision.

## Phase 6: provider readiness and fallback observability

Status: implemented locally. `/api/v1/readiness/providers` reports configuration state only, never calls providers, and never exposes secret values. Deterministic Platform job selection and candidate/job matching are explicitly reported as fallbacks.
