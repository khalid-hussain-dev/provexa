# PROVEXA — Data Models

> **Contract status: v0.2 — implementation baseline.**
>
> These models are the shared language between Platform and Intelligence modules.
> Keep the domain model stable during parallel development. Extend rather than silently rename.

## 1. Domain model

```text
User
 └── Candidate
      ├── Evidence ───────────────┐
      ├── Capability ─────────────┤
      ├── Resume ─────────────────┤
      ├── Interview ──────────────┤
      └── Course / Progress       │
                                  │
Job ── JobRequirement ────────────┘
 │
 └── Analysis
      ├── Match
      ├── Gaps
      ├── Evidence
      └── Recommendations

Interview
 ├── Questions
 ├── Answers
 └── Assessment

Course
 ├── Modules
 ├── Lessons
 └── Challenges
```

## 2. Identity and tenancy

### User

```text
User
- id: UUID
- name: string
- email: string
- password_hash: string
- two_factor_enabled: boolean
- created_at: datetime
- updated_at: datetime
```

### Candidate

A candidate is the career-facing profile belonging to a user.

```text
Candidate
- id: UUID
- user_id: UUID
- headline: string|null
- summary: string|null
- location: string|null
- preferences: JSONB
- created_at: datetime
- updated_at: datetime
```

A user has one primary candidate profile in the hackathon prototype.

## 3. Evidence

Evidence is the central primitive of PROVEXA.

```text
Evidence
- id: UUID
- candidate_id: UUID
- source_type: enum
- title: string
- content: text|null
- external_url: string|null
- metadata: JSONB
- confidence: float
- verification_status: enum
- created_at: datetime
- updated_at: datetime
```

### Source types

```text
CV
GITHUB
PORTFOLIO
INTERVIEW
LEARNING
OTHER
```

### Verification states

```text
CLAIMED
UNVERIFIED
PARTIALLY_VERIFIED
VERIFIED
```

### Important rule

AI may extract claims from evidence, but it must not upgrade evidence to `VERIFIED` merely because an LLM says it is true.

Verification is an evidence/state decision, not an LLM confidence label.

## 4. Capability

A capability represents something the candidate may be able to demonstrate.

```text
Capability
- id: UUID
- candidate_id: UUID
- skill_name: string
- category: string|null
- claimed_score: float
- evidence_score: float
- demonstrated_score: float
- confidence: float
- status: enum
- evidence_ids: JSONB
- updated_at: datetime
```

### Capability status

```text
CLAIMED
SUPPORTED
DEMONSTRATED
STRONG
GAP
```

Scores are normalized to `0–100`.

The exact readiness formula belongs to the application/service layer and must not be invented independently by each AI agent.

## 5. Job

```text
Job
- id: UUID
- title: string
- company: string
- location: string|null
- description: text
- seniority: string|null
- source: string
- source_url: string|null
- responsibilities: JSONB
- metadata: JSONB
- created_at: datetime
```

## 6. Job requirement

```text
JobRequirement
- id: UUID
- job_id: UUID
- skill_name: string
- importance: float
- requirement_type: enum
- evidence_expectation: string|null
- metadata: JSONB
```

### Requirement types

```text
REQUIRED
PREFERRED
RESPONSIBILITY
```

`importance` is normalized to `0–100`.

## 7. Candidate/job analysis

An analysis is a snapshot, not a live mutable score.

```text
Analysis
- id: UUID
- candidate_id: UUID
- job_id: UUID
- match_score: float
- readiness_score: float
- strengths: JSONB
- gaps: JSONB
- evidence_summary: JSONB
- recommendations: JSONB
- model_metadata: JSONB
- created_at: datetime
```

`model_metadata` may contain provider/model/version information for demo observability.

## 8. Interview

```text
Interview
- id: UUID
- candidate_id: UUID
- job_id: UUID
- status: enum
- current_question_index: integer
- overall_score: float|null
- technical_score: float|null
- communication_score: float|null
- problem_solving_score: float|null
- role_alignment_score: float|null
- verdict: enum|null
- created_at: datetime
- completed_at: datetime|null
```

### Interview status

```text
CREATED
IN_PROGRESS
COMPLETED
FAILED
```

### Verdict

```text
APPLY
APPLY_WITH_CAUTION
NOT_READY
```

## 9. Interview question

```text
InterviewQuestion
- id: UUID
- interview_id: UUID
- sequence: integer
- question: text
- competency: string
- difficulty: string
- expected_signals: JSONB
```

## 10. Interview answer

```text
InterviewAnswer
- id: UUID
- interview_id: UUID
- question_id: UUID
- answer: text
- score: float|null
- strengths: JSONB
- weaknesses: JSONB
- feedback: text|null
- created_at: datetime
```

## 11. Course

```text
Course
- id: UUID
- candidate_id: UUID
- job_id: UUID
- title: string
- objective: text
- estimated_duration: string
- status: enum
- created_at: datetime
```

### Course status

```text
GENERATED
IN_PROGRESS
COMPLETED
```

## 12. Course module

```text
CourseModule
- id: UUID
- course_id: UUID
- sequence: integer
- title: string
- objective: text
- content: JSONB
- challenge: JSONB
```

## 13. Learning progress

```text
LearningProgress
- id: UUID
- course_id: UUID
- module_id: UUID
- completion_percent: float
- assessment_score: float|null
- updated_at: datetime
```

## 14. Resume

```text
Resume
- id: UUID
- candidate_id: UUID
- job_id: UUID|null
- template: string
- version: integer
- content: JSONB
- evidence_references: JSONB
- created_at: datetime
```

### Evidence lock

Generated resume content should reference source evidence wherever practical.

The AI may improve wording, ordering, and emphasis, but it must not invent:

- employers
- job titles
- projects
- technologies
- years of experience
- certifications
- achievements
- metrics

## 15. Subscription demo

```text
Subscription
- id: UUID
- user_id: UUID
- plan: string
- status: enum
- provider: string
- external_reference: string|null
- created_at: datetime
```

For the hackathon, payment is simulated.

## 16. Relationships

```text
User 1 ─── 1 Candidate
Candidate 1 ─── N Evidence
Candidate 1 ─── N Capability
Candidate N ─── N Job (through Analysis)
Job 1 ─── N JobRequirement
Candidate 1 ─── N Interview
Interview 1 ─── N InterviewQuestion
Interview 1 ─── N InterviewAnswer
Candidate 1 ─── N Course
Course 1 ─── N CourseModule
CourseModule 1 ─── N LearningProgress
Candidate 1 ─── N Resume
User 1 ─── N Subscription
```

## 17. Ownership boundary

Platform owns persistence and CRUD.

Intelligence owns:

- extraction
- classification
- analysis
- recommendation generation
- interview reasoning
- course generation
- resume tailoring

Platform stores the resulting validated structures.

## 18. AI output rule

Every AI-generated object crossing into Platform must be:

```text
LLM output
 ↓
Pydantic/schema validation
 ↓
Business-rule validation
 ↓
Persistence
```

Raw model text is never treated as trusted structured data.
