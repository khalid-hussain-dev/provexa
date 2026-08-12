from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import InterviewAnswerRecord, InterviewQuestionRecord, InterviewRecord, JobRecord
from app.core.errors import NotFoundError


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


class InterviewService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_interview(self, candidate_id: str, job: JobRecord) -> tuple[InterviewRecord, InterviewQuestionRecord]:
        interview = InterviewRecord(
            id=str(uuid4()),
            candidate_id=candidate_id,
            job_id=job.id,
            status="CREATED",
            current_question_index=0,
        )
        self._session.add(interview)
        self._session.flush()

        questions = self._build_questions(job)
        records: list[InterviewQuestionRecord] = []
        for index, question in enumerate(questions, start=1):
            record = InterviewQuestionRecord(
                id=str(uuid4()),
                interview_id=interview.id,
                sequence=index,
                question=question["question"],
                competency=question["competency"],
                difficulty=question["difficulty"],
                expected_signals=question["expected_signals"],
            )
            self._session.add(record)
            records.append(record)

        self._session.commit()
        self._session.refresh(interview)
        first_question = records[0]
        return interview, first_question

    def answer_question(self, interview_id: str, question_id: str, answer: str) -> tuple[InterviewAnswerRecord, InterviewQuestionRecord | None]:
        interview = self._session.get(InterviewRecord, interview_id)
        if interview is None:
            raise NotFoundError("Interview not found", {"interview_id": interview_id})

        question = self._session.get(InterviewQuestionRecord, question_id)
        if question is None or question.interview_id != interview_id:
            raise NotFoundError("Interview question not found", {"question_id": question_id})

        existing = self._session.scalar(
            select(InterviewAnswerRecord).where(
                InterviewAnswerRecord.interview_id == interview_id,
                InterviewAnswerRecord.question_id == question_id,
            )
        )
        if existing is None:
            existing = InterviewAnswerRecord(
                id=str(uuid4()),
                interview_id=interview_id,
                question_id=question_id,
                answer=answer,
            )
            self._session.add(existing)
        else:
            existing.answer = answer

        score = self._score_answer(question.expected_signals, answer)
        existing.score = score
        existing.feedback = self._feedback_for_score(score, question.competency)
        existing.strengths = [signal for signal in question.expected_signals if signal in _normalize_text(answer)]
        existing.weaknesses = [signal for signal in question.expected_signals if signal not in _normalize_text(answer)]

        interview.status = "IN_PROGRESS"
        interview.current_question_index = max(interview.current_question_index, question.sequence)

        next_question = self._session.scalar(
            select(InterviewQuestionRecord)
            .where(
                InterviewQuestionRecord.interview_id == interview_id,
                InterviewQuestionRecord.sequence == question.sequence + 1,
            )
        )
        self._session.commit()
        return existing, next_question

    def complete_interview(self, interview_id: str) -> dict:
        interview = self._session.get(InterviewRecord, interview_id)
        if interview is None:
            raise NotFoundError("Interview not found", {"interview_id": interview_id})

        questions = list(
            self._session.scalars(
                select(InterviewQuestionRecord).where(InterviewQuestionRecord.interview_id == interview_id).order_by(InterviewQuestionRecord.sequence)
            )
        )
        answers = {
            answer.question_id: answer
            for answer in self._session.scalars(select(InterviewAnswerRecord).where(InterviewAnswerRecord.interview_id == interview_id))
        }

        if not answers:
            raise NotFoundError("Interview has no answers", {"interview_id": interview_id})

        scores = [answer.score or 0 for answer in answers.values()]
        overall_score = round(sum(scores) / len(scores))

        technical_scores = [
            answer.score or 0
            for question in questions
            if question.competency.lower() not in {"communication", "behavioral"}
            if (answer := answers.get(question.id))
        ]
        communication_scores = [
            answer.score or 0
            for question in questions
            if question.competency.lower() in {"communication", "behavioral"}
            if (answer := answers.get(question.id))
        ]
        problem_solving_scores = [
            answer.score or 0
            for question in questions
            if "design" in question.competency.lower() or "problem" in question.competency.lower()
            if (answer := answers.get(question.id))
        ]

        technical_score = round(sum(technical_scores) / len(technical_scores)) if technical_scores else overall_score
        communication_score = round(sum(communication_scores) / len(communication_scores)) if communication_scores else overall_score
        problem_solving_score = round(sum(problem_solving_scores) / len(problem_solving_scores)) if problem_solving_scores else overall_score

        job_requirements = list(getattr(interview.job, "requirements", []) or [])
        requirement_skills = {requirement.skill_name.lower() for requirement in job_requirements}
        matched_skills = set()
        for question in questions:
            answer = answers.get(question.id)
            if not answer:
                continue
            matched_skills.update({signal for signal in (answer.strengths or []) if signal})
        role_alignment_score = min(100, round((overall_score * 0.6) + (len(requirement_skills & matched_skills) * 8)))

        verdict = "APPLY" if overall_score >= 85 else "APPLY_WITH_CAUTION" if overall_score >= 65 else "NOT_READY"
        strengths = [
            {"competency": question.competency, "score": round(answers[question.id].score or 0)}
            for question in questions
            if answers.get(question.id) and (answers[question.id].score or 0) >= 75
        ]
        gaps = [
            {"competency": question.competency, "score": round(answers[question.id].score or 0), "target": 80}
            for question in questions
            if answers.get(question.id) and (answers[question.id].score or 0) < 75
        ]
        recommendations = [
            {"competency": item["competency"], "action": f"Practice and strengthen {item['competency']} responses"}
            for item in gaps[:3]
        ]

        interview.status = "COMPLETED"
        interview.overall_score = overall_score
        interview.technical_score = technical_score
        interview.communication_score = communication_score
        interview.problem_solving_score = problem_solving_score
        interview.role_alignment_score = role_alignment_score
        interview.verdict = verdict
        interview.completed_at = datetime.now(timezone.utc)
        self._session.commit()

        return {
            "overall_score": overall_score,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "problem_solving_score": problem_solving_score,
            "role_alignment_score": role_alignment_score,
            "verdict": verdict,
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations,
        }

    def _build_questions(self, job: JobRecord) -> list[dict]:
        requirements = list(getattr(job, "requirements", []) or [])
        first_skill = requirements[0].skill_name if requirements else "Python"
        second_skill = requirements[1].skill_name if len(requirements) > 1 else "System Design"
        third_skill = requirements[2].skill_name if len(requirements) > 2 else "Communication"
        return [
            {
                "question": f"Tell me about a recent {first_skill} feature you shipped and the trade-offs you made.",
                "competency": first_skill,
                "difficulty": "MEDIUM",
                "expected_signals": [first_skill.lower(), "ownership", "impact", "trade-off"],
            },
            {
                "question": f"How would you design and scale a backend service for a {job.title.lower()} role, especially around {second_skill.lower()}?",
                "competency": "System Design",
                "difficulty": "MEDIUM",
                "expected_signals": [second_skill.lower(), "scalability", "database", "testing"],
            },
            {
                "question": f"Share a time you handled an unclear production issue or team disagreement while delivering software.",
                "competency": "Communication",
                "difficulty": "MEDIUM",
                "expected_signals": ["communication", "debug", "collaboration", "resolution"],
            },
        ]

    def _score_answer(self, expected_signals: list[str], answer: str) -> int:
        normalized = _normalize_text(answer)
        score = 35 + min(25, len(normalized) // 18)
        for signal in expected_signals:
            if signal.lower() in normalized:
                score += 12
        if any(word in normalized for word in ("because", "trade-off", "tradeoff", "example", "result", "impact")):
            score += 8
        return max(0, min(100, score))

    def _feedback_for_score(self, score: int, competency: str) -> str:
        if score >= 85:
            return f"Strong {competency} response with clear reasoning and practical detail."
        if score >= 65:
            return f"Solid {competency} response, but it could include more concrete examples."
        return f"{competency} response needs more detail, structure, and evidence."
