# PROVEXA — API Contracts

> **Contract status: v0.2 — implementation baseline.**
>
> These contracts are intentionally REST-oriented and stable enough for parallel frontend/backend development.
> Implementations may evolve internally without changing the public contract.

## 1. Global conventions

Base path:

```text
/api/v1
```

Authentication:

```text
Authorization: Bearer <access_token>
```

Content type:

```text
application/json
```

IDs:

```text
UUID
```

Dates:

```text
ISO-8601
```

All protected endpoints require authentication unless explicitly stated.

## 2. Standard success/error envelope

Successful resources may be returned directly.

Errors MUST use:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

The `details` object is optional.

## 3. Authentication

### POST `/auth/signup`

```json
{
  "name": "Khalid",
  "email": "user@example.com",
  "password": "string"
}
```

Response:

```json
{
  "user_id": "uuid",
  "requires_2fa_setup": false
}
```

### POST `/auth/login`

Response:

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "requires_2fa": true
}
```

If 2FA is required, the token must not grant protected access until verification is complete.

### POST `/auth/2fa/verify`

```json
{
  "code": "123456"
}
```

Response:

```json
{
  "authenticated": true,
  "access_token": "string"
}
```

### POST `/auth/forgot-password`

```json
{
  "email": "user@example.com"
}
```

For the hackathon, the flow may be simulated.

## 4. Candidate

### GET `/candidate`

Response:

```json
{
  "id": "uuid",
  "name": "string",
  "headline": "string",
  "summary": "string",
  "location": "string",
  "preferences": {}
}
```

### PUT `/candidate`

Accepts candidate profile fields.

### POST `/candidate/evidence`

Request:

```json
{
  "source_type": "CV",
  "title": "Khalid Resume",
  "content": "text",
  "external_url": null
}
```

Response:

```json
{
  "evidence_id": "uuid",
  "status": "stored"
}
```

## 5. Analysis

### POST `/analysis/candidate`

Starts candidate evidence analysis.

Response:

```json
{
  "analysis_id": "uuid",
  "status": "completed",
  "capabilities": []
}
```

### POST `/analysis/job`

Request:

```json
{
  "job_description": "string",
  "title": "Backend Developer",
  "company": "Example"
}
```

Response:

```json
{
  "job_id": "uuid",
  "requirements": []
}
```

### POST `/analysis/match`

Request:

```json
{
  "job_id": "uuid"
}
```

Response:

```json
{
  "analysis_id": "uuid",
  "match_score": 82,
  "readiness_score": 76,
  "strengths": [
    {
      "skill": "Python",
      "score": 94,
      "evidence": []
    }
  ],
  "gaps": [
    {
      "skill": "Kubernetes",
      "required_score": 80,
      "candidate_score": 25,
      "importance": 90
    }
  ],
  "recommendations": [],
  "evidence_summary": []
}
```

## 6. GitHub

### POST `/github/connect`

```json
{
  "username": "github-user"
}
```

### POST `/github/analyze`

```json
{
  "username": "github-user"
}
```

Response:

```json
{
  "evidence_id": "uuid",
  "repositories_analyzed": 8,
  "capabilities": []
}
```

## 7. Jobs

### GET `/jobs`

Query parameters:

```text
page
limit
source
query
location
```

### GET `/jobs/{job_id}`

Returns normalized job information.

### POST `/jobs/recommend`

Request:

```json
{
  "limit": 10,
  "location": null
}
```

Response:

```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "title": "Backend Developer",
      "company": "Example",
      "match_score": 88,
      "readiness_score": 81,
      "source": "provider"
    }
  ]
}
```

## 8. Interviews

### POST `/interviews`

Request:

```json
{
  "job_id": "uuid"
}
```

Response:

```json
{
  "interview_id": "uuid",
  "status": "CREATED",
  "first_question": {
    "question_id": "uuid",
    "question": "string",
    "competency": "Python"
  }
}
```

### POST `/interviews/{interview_id}/answer`

Request:

```json
{
  "question_id": "uuid",
  "answer": "string"
}
```

Response:

```json
{
  "score": 82,
  "feedback": "string",
  "next_question": {
    "question_id": "uuid",
    "question": "string",
    "competency": "System Design"
  }
}
```

If the interview is complete:

```json
{
  "score": 82,
  "feedback": "string",
  "next_question": null
}
```

### POST `/interviews/{interview_id}/complete`

Response:

```json
{
  "overall_score": 82,
  "technical_score": 86,
  "communication_score": 78,
  "problem_solving_score": 84,
  "role_alignment_score": 80,
  "verdict": "APPLY_WITH_CAUTION",
  "strengths": [],
  "gaps": [],
  "recommendations": []
}
```

## 9. Courses

### POST `/courses/generate`

Request:

```json
{
  "job_id": "uuid",
  "interview_id": "uuid"
}
```

Response:

```json
{
  "course_id": "uuid",
  "status": "GENERATED",
  "title": "Backend Readiness Sprint",
  "estimated_duration": "14 days",
  "modules": []
}
```

### GET `/courses/{course_id}`

Returns complete course content.

### POST `/courses/{course_id}/progress`

```json
{
  "module_id": "uuid",
  "completion_percent": 75,
  "assessment_score": 84
}
```

## 10. Resumes

### GET `/resumes/templates`

Response:

```json
{
  "templates": [
    {
      "id": "minimal",
      "name": "Minimal Professional",
      "preview": null
    }
  ]
}
```

### POST `/resumes/generate`

Request:

```json
{
  "job_id": "uuid",
  "template": "minimal"
}
```

Response:

```json
{
  "resume_id": "uuid",
  "version": 1,
  "content": {},
  "evidence_references": []
}
```

## 11. Subscription demo

### POST `/subscription/checkout`

```json
{
  "plan": "PRO"
}
```

Response:

```json
{
  "checkout_id": "uuid",
  "status": "PENDING"
}
```

### POST `/subscription/confirm`

```json
{
  "checkout_id": "uuid"
}
```

Response:

```json
{
  "status": "ACTIVE",
  "demo_payment": true
}
```

## 12. Async behavior

AI-heavy endpoints may eventually become asynchronous.

For the hackathon, synchronous responses are acceptable when they complete quickly.

If an operation becomes asynchronous, use:

```json
{
  "operation_id": "uuid",
  "status": "PROCESSING"
}
```

and expose a status endpoint.

Do not create a different async pattern for every feature.

## 13. Provider abstraction

Frontend must never know whether a result came from:

```text
Groq
Gemini
NVIDIA NIM
Mock/seeded data
```

That decision belongs behind the backend/intelligence boundary.

## 14. Contract change protocol

A breaking change requires:

1. Update this document.
2. Update affected task documentation.
3. Update frontend API client.
4. Update backend implementation.
5. Update integration checklist.
6. Add/modify an integration test.

Never silently change a response field after another module has started consuming it.
