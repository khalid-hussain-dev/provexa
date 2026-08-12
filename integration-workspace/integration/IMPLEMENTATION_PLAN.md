# Copy-Based Integration Implementation Plan

Status: planning only. Experience Builder is excluded.

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

## Phase 3: first AI workflow connection

Status: Phase 2 candidate/profile-analysis adapter implemented locally. The existing Intelligence profile route and workflow files remain unchanged. The protected integration route validates and persists only an allowlisted profile snapshot.

1. Connect candidate/evidence payloads to the existing Intelligence profile workflow.
2. Validate the returned profile context and map it to Platform capability/evidence records.
3. Preserve deterministic fallback when AI configuration or providers are unavailable.
4. Run candidate analysis and persistence tests before proceeding.

## Phase 4: interview connection

1. Preserve Platform answer persistence.
2. Use existing Intelligence question generation where the candidate/job mapping is valid.
3. Submit complete transcripts to the existing Intelligence evaluator.
4. Validate and persist the final verdict, scores, strengths, gaps, and recommendations.

## Phase 5: course and resume compatibility

1. Map existing Intelligence course modules into Platform course records.
2. Keep Platform progress persistence authoritative.
3. Test resume optimization only with explicit source text and evidence references.
4. Keep Platform evidence lock authoritative; never infer verification from AI output.

## Phase 6: local golden-path validation

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

Create only the adapter/DTO skeleton and fake-provider contract tests inside the copied workspace. Do not wire live production routes, modify Intelligence workflow code, or require API keys in that batch.
