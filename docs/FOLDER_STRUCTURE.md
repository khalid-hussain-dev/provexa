# PROVEXA — Folder Structure

```text
PROVEXA/
│
├── frontend/                       # Experience Builder ownership
│
├── backend/                        # Platform Builder ownership
│   ├── app/
│   ├── api/
│   ├── auth/
│   ├── candidates/
│   ├── evidence/
│   ├── jobs/
│   ├── interviews/
│   ├── courses/
│   ├── resumes/
│   ├── database/
│   └── redis/
│
├── services/                       # Intelligence Builder ownership
│   ├── ai/
│   │   ├── crews/
│   │   ├── agents/
│   │   ├── tasks/
│   │   ├── prompts/
│   │   ├── validators/
│   │   └── llm_gateway/
│   │
│   ├── github/
│   ├── jobs/
│   └── integrations/
│
├── gigs/
│   ├── authkit/
│   └── jobfit/
│
├── tests/
│
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── TECH_STACK.md
│   ├── FOLDER_STRUCTURE.md
│   ├── PROJECT_STRUCTURE.txt
│   ├── API_CONTRACTS.md
│   ├── DATA_MODELS.md
│   ├── INTEGRATION_GUIDE.md
│   ├── INTEGRATION_CHECKLIST.md
│   ├── ENVIRONMENT.md
│   ├── CONTRIBUTING.md
│   ├── ARCHITECTURE_DECISIONS.md
│   └── tasks/
│       ├── EXPERIENCE_BUILDER.md
│       ├── PLATFORM_BUILDER.md
│       ├── INTELLIGENCE_BUILDER.md
│       └── INTEGRATION_LEAD.md
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Ownership

### Experience Builder
Primary ownership: `/frontend`

### Platform Builder
Primary ownership: `/backend`

### Intelligence Builder
Primary ownership: `/services` and AI-related integration code

### Integration Lead
May modify any module during integration, but should avoid unnecessary rewrites.

## Shared rules

- Do not silently move directories.
- Do not rename shared models without updating contracts.
- Do not introduce a dependency on another module's internal files.
- Changes affecting shared contracts must be documented.
