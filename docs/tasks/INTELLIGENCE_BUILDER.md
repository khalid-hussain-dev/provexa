# PROVEXA — Intelligence Builder Task

## Role

You are the **Intelligence Builder**.

You own PROVEXA's AI orchestration and external integrations.

## Read first

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `TECH_STACK.md`
- `FOLDER_STRUCTURE.md`
- `API_CONTRACTS.md`
- `DATA_MODELS.md`
- `ARCHITECTURE_DECISIONS.md`
- `CONTRIBUTING.md`

## Primary ownership

```text
/services/**
```

## Mission

Build the intelligence layer that turns candidate/job evidence into analysis, assessment, learning, and application intelligence.

## AI workflows

### Candidate Intelligence Crew

- Evidence analysis
- Skill extraction
- Capability mapping
- Gap analysis

### Interview Intelligence Crew

- Job-specific interview planning
- Adaptive questions
- Answer evaluation
- Evidence validation
- Readiness judgment

### Learning Intelligence Crew

- Gap analysis
- Curriculum generation
- Practical challenge generation
- Assessment generation

### Resume intelligence

- Job-specific tailoring
- Evidence-backed content generation
- Structured resume output

## Integration responsibilities

- GitHub adapter
- Job-provider adapters
- LLM gateway
- Provider fallback
- AI output validation
- AI caching

## Rules

- Do not expose provider keys to the frontend.
- Do not hard-code one provider throughout the system.
- Do not allow raw LLM output to become trusted database state.
- Validate structured outputs.
- Keep external providers behind adapters.
- Provide mock/seeded fallback where practical.
- Do not modify `/frontend`.

## Completion criteria

- Core AI workflows can be invoked through stable service interfaces.
- LLM provider can be swapped through the gateway.
- Structured responses are validated.
- Provider failures are handled.
- GitHub/job integrations have stable interfaces.
- Demo-safe fallbacks exist.
