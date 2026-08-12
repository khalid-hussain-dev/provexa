# PROVEXA Intelligence Builder Progress

Last updated: 2026-08-12

Repository: `E:\PROVEXA\crew-provexa`
Branch: `mohib`

## Scope

- Primary ownership: `/services/**` conceptually, with this repo acting as the Intelligence Builder module.
- Core mission: AI orchestration, profile analysis, interview generation/evaluation, learning-path generation, resume optimization, and job recommendation.
- This ledger is documentation-only; no code changes were made while reviewing the module.

## High-level assessment

The module is functionally rich and appears aimed at a full demo loop:

1. Parse candidate evidence from resume and web/GitHub sources.
2. Build a candidate profile context with CrewAI.
3. Generate interview questions.
4. Evaluate responses and produce percentage-based skill scores.
5. Generate a targeted learning course.
6. Optimize a resume with new skills.
7. Recommend jobs.

The repo is closer to a self-contained intelligence demo than a thin library; it includes crews, orchestration, CLI/demo flows, helper utilities, and tests.

## File-by-file understanding

| File | What it does | Notes |
|---|---|---|
| `config.py` | Loads LLM, GitHub, job API, DB, and Redis settings from `.env`. | Uses `pydantic-settings`; requires `GEMINI_API_KEY`. |
| `models.py` | Defines Pydantic domain models for profiles, questions, responses, assessments, courses, resumes, jobs, and final assessment. | Central schema layer for the module. |
| `utils.py` | Parses CrewAI output robustly and patches LiteLLM behavior. Provides default LLM selection with Gemini → Groq fallback. | Important glue for keeping CrewAI output stable. |
| `agents.py` | Defines reusable CrewAI agents for profile analysis, interviewing, evaluation, courses, and career advice. | Agent factory only; no workflows. |
| `profile_analyzer.py` | Extracts resume text, analyzes GitHub profiles, analyzes web/portfolio pages, extracts skills, and creates profile summaries. | Handles external signals and evidence gathering. |
| `profile_analysis_crew.py` | Runs the profile-analysis crew: resume extraction, GitHub analysis, domain classification, and synthesis. | Produces the candidate context used downstream. |
| `interview_crew.py` | Generates interview questions and evaluates interview responses using CrewAI. | Handles question generation, strength/weakness analysis, and skill scoring. |
| `course_crew.py` | Selects priority skill gaps, generates a targeted course, and performs ATS resume optimization. | Covers learning-path generation and resume tailoring. |
| `job_service.py` | Recommends jobs using Adzuna when possible, otherwise mock recommendations. Also calculates skill match. | External integration with fallback behavior. |
| `interview_system.py` | Orchestrates the full pipeline: profile prep, question generation, response evaluation, course generation, resume optimization. | Main service coordinator for the Intelligence Builder. |
| `main.py` | Exposes FastAPI endpoints for profile analysis, interview question generation, interview evaluation, job recommendation, and complete assessment. | This is the main runnable API surface. |
| `cli_interview.py` | Interactive terminal workflow for the full demo loop. | Useful for ceremonies/demos; depends on live AI/services. |
| `example_usage.py` | Programmatic example showing the end-to-end flow. | Demonstrative, not a hardened production entrypoint. |
| `test_setup.py` | Dependency/import/model sanity script. | More of a manual verification helper than an automated test suite. |
| `test_utils.py` | Lightweight checks for output parsing and list parsing helpers. | Focused utility validation. |
| `test_new_features.py` | Demo-oriented async script for new course/resume features. | Useful for manual verification. |
| `README.md` | Explains the product story, features, architecture, install, API usage, and workflows. | Good high-level product documentation. |
| `requirements.txt` | Python dependencies for CrewAI, FastAPI, GitHub, parsing, and async file handling. | Includes the expected AI stack. |

## Implemented capabilities

- Candidate profile analysis from:
  - resume files
  - GitHub profiles
  - LinkedIn / portfolio web pages
  - manually provided skills and additional info
- CrewAI-based profile synthesis into a structured context.
- Domain classification and interview-depth calibration.
- Interview question generation with:
  - category
  - difficulty
  - focus
  - domain
- Interview evaluation with:
  - overall score
  - skill assessments
  - strengths
  - weaknesses
  - improvement areas
  - readiness level
- Targeted course generation:
  - selects 2–3 priority skills
  - builds modules with concept explanation, code example, validation exercise, and hint
- Resume optimization:
  - injects newly learned skills into existing resume text
  - preserves the resume rather than rewriting it from scratch
- Job recommendation:
  - Adzuna integration path
  - mock fallback if API access is unavailable
- Demo orchestration:
  - FastAPI API
  - CLI walkthrough
  - example usage script
  - helper tests

## Comparison chart: implemented vs. still left

| Area | Implemented | Still left / caveat | Completion |
|---|---|---|---:|
| Profile analysis | Resume/GitHub/web profile ingestion, skill extraction, synthesis | None major in this repo | 100% |
| Interview generation | Domain-specific question generation | None major in this repo | 100% |
| Interview evaluation | Response scoring, strengths/weaknesses, readiness | None major in this repo | 100% |
| Course generation | Priority-gap selection, module generation | None major in this repo | 100% |
| Resume optimization | ATS-style targeted skill injection | None major in this repo | 100% |
| Job recommendations | Adzuna integration + mock fallback | Real API availability depends on env keys | 95% |
| API layer | FastAPI endpoints for the full flow | Not packaged as a separate deployable microservice | 95% |
| CLI/demo tooling | Interactive CLI and example scripts | Some scripts are demo-oriented and may need async/runtime polish | 90% |
| Tests/helpers | Utility checks and feature smoke scripts | No formal pytest suite across the whole module | 75% |
| External reliability | Fallbacks and defensive parsing exist | Real-world API secrets and provider stability still matter | 85% |

Overall module readiness estimate: about 92%

## Notes and caveats

- This repo is clearly the Intelligence Builder boundary; it should stay separate from the Platform Builder backend.
- The module already contains the logic for profile analysis, interview generation/evaluation, learning-path generation, resume optimization, and job recommendations.
- `course_crew.py` exists and is the missing link that `interview_system.py` imports.
- The repo uses CrewAI heavily, so runtime quality depends on the configured LLM provider and API keys.
- The helper scripts are useful for demos and local checks, but they are not the same thing as a formal test suite.
- Some example/demo files are more illustrative than production-hardened.

## Suggested next review items

- Confirm the expected environment variables for Gemini/Groq/GitHub/Adzuna in the deployment notes.
- Decide whether the API surface should remain in this repo or be consumed as a service boundary by PROVEXA Platform Builder.
- If a formal release is desired, add a real automated test suite around the main orchestration flows.

