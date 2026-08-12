# PROVEXA — Contribution Rules

## 1. Ownership

### Experience Builder
Owns `/frontend`.

### Platform Builder
Owns `/backend`.

### Intelligence Builder
Owns `/services` and AI/integration modules.

### Integration Lead
Owns final integration and may modify modules when required.

## 2. Shared contract rules

- Read documentation before coding.
- Do not invent endpoints.
- Do not silently change shared schemas.
- Do not modify another builder's module during parallel development.
- Use mocks for unfinished dependencies.
- Document deviations.

## 3. Commits

Use small descriptive commits.

Examples:

```text
feat(auth): add signup endpoint
feat(candidate): add evidence model
feat(ai): add job analyzer
feat(ui): add interview dashboard
fix(github): handle repository timeout
```

Avoid:

```text
feat: build everything
```

## 4. Dependencies

Before adding a new dependency:

1. Confirm it is necessary.
2. Add it to the appropriate dependency file.
3. Record it in documentation if architecturally significant.

## 5. Secrets

Never commit:

- API keys
- passwords
- tokens
- production credentials
- private certificates

## 6. AI-generated code

AI-generated code must still:

- follow project architecture
- respect ownership
- validate inputs
- handle failures
- avoid unnecessary dependencies
- be understandable by the integration team
