# PROVEXA Presentation Guide

## 1. One-minute product explanation

**PROVEXA helps candidates turn potential into proof.**

Instead of only collecting a CV, it connects candidate-owned evidence to a target role, identifies strengths and gaps, runs a role-specific interview, creates a learning path, and produces an evidence-backed resume preview.

The product journey is:

```text
Evidence -> Assessment -> Readiness -> Improvement -> Proof
```

Use this sentence to open the presentation:

> "PROVEXA is a career-readiness instrument. It helps a candidate understand what they can prove today, what a target job needs, and the next action that improves their readiness."

## 2. Architecture in simple terms

| Layer | Responsibility | What to say |
| --- | --- | --- |
| Experience | React frontend | "This is the candidate workspace and guided journey." |
| Platform | FastAPI, PostgreSQL, Redis | "This layer owns accounts, authorization, durable records, and session state." |
| Intelligence | Existing AI workflows and provider adapters | "This layer analyzes evidence, generates interview material, evaluates answers, and creates learning/resume guidance." |
| Integration | Adapters between all three layers | "The integration boundary validates AI output before Platform persistence and keeps ownership checks in place." |

Important framing:

- PostgreSQL is the durable source of truth.
- Redis is the server-side session authority.
- The frontend calls the integrated API host; it does **not** call AI providers directly.
- Candidate records are protected through authenticated ownership checks.

## 3. Feature map

| Feature | User value | Presentation wording |
| --- | --- | --- |
| Authentication | Keeps every journey candidate-scoped | "A candidate signs in, and protected actions use a bearer session." |
| Candidate profile | Captures role, experience, skills, and preferences | "The candidate starts by making their professional context structured and usable." |
| Evidence capture | Stores CV text, GitHub/portfolio references, and notes | "PROVEXA works from evidence; it does not invent qualifications." |
| Profile analysis | Converts evidence into a validated profile context | "We identify supported skills, likely strengths, and areas where proof is thin." |
| Target jobs | Lets a candidate choose an opportunity | "The candidate chooses the role worth proving readiness for." |
| Candidate/job match | Shows readiness, strengths, gaps, and recommendations | "The assessment is explainable: it shows why the match exists." |
| Interview Arena | Captures answers to role-specific questions | "The interview is tied to the selected job and the candidate's owned context." |
| Interview verdict | Gives a score, strengths, gaps, and next action | "The verdict translates performance into a concrete readiness decision." |
| Learning path | Generates course modules and stores progress | "The gap becomes a focused plan rather than a generic course catalogue." |
| Resume tailoring | Produces a preview based on selected CV evidence and course work | "The final resume emphasizes verified evidence relevant to the target role." |
| Subscription demo | Demonstrates a possible commercial surface | "This is a frontend demonstration, not a live payment integration." |

## 4. Recommended live demo: reliable presentation mode

For a presentation today, use **demo mode** unless the full production-like host has been provisioned and verified.

From `E:\PROVEXA\integration-workspace\frontend`:

```powershell
npm install
$env:VITE_API_MODE = "demo"
npm run dev
```

Open the URL printed by Vite. Demo mode is intentional: it uses deterministic local data, clearly labels the workspace as Demo, and does not hide a live API failure.

Do not call demo mode "live AI" or "live database persistence."

## 5. Click-by-click demo script (7-10 minutes)

### Step 1 — Enter the workspace

1. Open the landing page.
2. Point out the product line: **From potential to proof.**
3. Click **Enter seeded demo workspace**.

Say:

> "We start with an authenticated candidate workspace. Every later record belongs to this candidate."

### Step 2 — Create the evidence record

1. On **Evidence**, briefly show the candidate record fields.
2. Paste or use the seeded CV/evidence text.
3. Click **Save and analyze**.
4. Point to the evidence inventory and profile context.

Say:

> "The first requirement is evidence. We capture source material before making any recommendation, so the system can show what supports its conclusions."

Highlight:

- Candidate profile fields
- CV evidence
- Validated skills and weaknesses
- Candidate-scoped evidence inventory

### Step 3 — Choose a target job and inspect the match

1. Click **Continue to target opportunities**.
2. Select **Backend Developer** using **Select and assess**.
3. Point out the match score, readiness score, strengths, and gap.

Say:

> "The selected job becomes the assessment target. PROVEXA makes the reasoning visible: what matches, what is missing, and what to improve next."

### Step 4 — Run the Interview Arena

1. Answer each of the three questions with short, concrete responses.
2. Click **Record answer** after each response.
3. After the last question, click **View interview verdict**.

Say:

> "The interview is job-specific. Answers are recorded against the candidate and selected role, while evaluation semantics remain in the Intelligence layer."

### Step 5 — Explain the readiness verdict

1. On **Readiness**, show the verdict label and scores.
2. Show the strengths and the thin-proof area.
3. Click **Generate learning path**.

Say:

> "The verdict is not just a score. It explains what is already credible and identifies the next best action."

### Step 6 — Complete the learning path

1. Complete the first module challenge.
2. Open and complete the second module challenge.
3. Point out progress reaching 100%.
4. Click **Continue to resume builder**.

Say:

> "The learning path is personalized to the gaps identified in the assessment. Progress is kept against the candidate course."

### Step 7 — Generate the evidence-backed resume preview

1. On **Resume**, show the evidence lock and selected course.
2. Click **Optimize with verified evidence**.
3. Compare the source evidence with the tailored preview.
4. Optionally click **Export text preview**.

Say:

> "The resume changes are constrained by the owned CV evidence and completed learning path. It highlights proof; it does not fabricate experience."

## 6. Suggested closing

> "PROVEXA turns an unclear career question — ‘Am I ready?’ — into an evidence-backed sequence: document capability, assess a real role, practice under pressure, close focused gaps, and present the proof clearly."

## 7. Questions the team may receive

### "Is this just a CV analyzer?"

No. The CV/evidence is the starting point. The product continues through job matching, an interview, a verdict, targeted learning progress, and job-specific resume tailoring.

### "Why is evidence important?"

It makes recommendations auditable. The system can distinguish between an unsupported claim and a capability backed by supplied evidence.

### "Where does AI fit?"

AI is used for reasoning-heavy work such as profile interpretation, interview generation/evaluation, and tailored learning/resume guidance. Platform validation, authorization, persistence, and routing remain deterministic software responsibilities.

### "Does the frontend call Gemini, Groq, or GitHub directly?"

No. The frontend calls the integrated API host only. Provider access is owned by the backend/Intelligence side.

### "Is the resume a PDF export?"

The current presentation build provides a browser-local text preview/export. PDF/DOCX parsing and document export are not part of the current implemented scope.

### "Is payment live?"

No. Subscription/payment is a frontend demonstration surface only.

## 8. Honest current-status statement

Use this wording if asked about deployment readiness:

> "The code-level integration is implemented and covered by local integration tests. The presentation can use deterministic demo mode. Production-like verification with provisioned PostgreSQL, Redis, AI providers, and a browser against the live host remains an operational readiness task."

### Current limitations to state clearly

- Live PostgreSQL, Redis, and provider calls are not yet verified end-to-end.
- The present local environment needs a valid PostgreSQL configuration and installed Python runtime dependencies before the composed live host can start.
- A user-facing two-factor enrollment screen is available from the workspace header. It displays an authenticator key for manual TOTP enrollment, then verifies the current six-digit code. Live enrollment still requires the composed host, PostgreSQL, Redis, and a valid JWT configuration.
- Evidence inventory in the frontend is session-local because there is no mounted evidence-list endpoint.
- Pasted CV text is required; resume PDF/DOCX text extraction is not implemented.
- Resume export and subscription/payment behavior are frontend-local demonstrations.

## 9. Presenter checklist

Before presenting:

- [ ] Start the frontend in `VITE_API_MODE=demo`.
- [ ] Confirm the landing page says demo mode is active.
- [ ] Use the seeded demo workspace.
- [ ] Keep the presentation on the six numbered journey steps.
- [ ] Use concise, evidence-first language rather than promising unverified live-provider behavior.
- [ ] Do not display `.env` files, provider keys, passwords, tokens, or database URLs.

## 10. Internal handoff

For operational setup and validation, use `LOCAL_RUNBOOK.md` in this directory. For the exact connected API routes and verification boundary, use `EXPERIENCE_INTEGRATION_STATUS.md`.
