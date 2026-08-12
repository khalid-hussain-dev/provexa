from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import CourseModuleRecord, CourseRecord, LearningProgressRecord
from app.core.errors import NotFoundError


class CourseService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def generate_course(self, candidate_id: str, job, interview) -> tuple[CourseRecord, list[CourseModuleRecord]]:
        questions = list(interview.questions)
        strengths = [question.competency for question in questions]
        module_specs = [
            (
                "Core role alignment",
                f"Reinforce the core stack for {job.title}.",
                {
                    "lessons": [f"Review the practical use of {strengths[0] if strengths else 'Python'} in your shipped work."],
                    "references": [question.question for question in questions[:1]],
                },
                {
                    "exercise": "Summarize one project using the target stack and identify two improvement points.",
                },
            ),
            (
                "System design and delivery",
                "Practice architectural reasoning, trade-offs, and delivery planning.",
                {
                    "lessons": ["Model the service boundary, persistence layer, and API contract.", "Document trade-offs explicitly."],
                    "references": [question.question for question in questions[1:2]],
                },
                {
                    "exercise": "Draft an API design for a similar feature in 20 minutes.",
                },
            ),
            (
                "Interview readiness and communication",
                "Tighten answers, evidence framing, and professional communication.",
                {
                    "lessons": ["Use evidence-backed examples.", "Lead with outcome, then constraints, then action."],
                    "references": [question.question for question in questions[2:3]],
                },
                {
                    "exercise": "Answer a behavioral prompt in STAR format.",
                },
            ),
        ]

        course = CourseRecord(
            id=str(uuid4()),
            candidate_id=candidate_id,
            job_id=job.id,
            title=f"{job.title} Readiness Sprint",
            objective=f"Close the gaps for {job.title} and strengthen interview performance.",
            estimated_duration="14 days",
            status="GENERATED",
            modules=[],
        )
        self._session.add(course)
        self._session.flush()

        module_rows: list[CourseModuleRecord] = []
        for sequence, (title, objective, content, challenge) in enumerate(module_specs, start=1):
            module = CourseModuleRecord(
                id=str(uuid4()),
                course_id=course.id,
                sequence=sequence,
                title=title,
                objective=objective,
                content=content,
                challenge=challenge,
            )
            self._session.add(module)
            module_rows.append(module)

        course.modules = [
            {
                "module_id": None,
                "sequence": sequence,
                "title": title,
                "objective": objective,
                "content": content,
                "challenge": challenge,
            }
            for sequence, (title, objective, content, challenge) in enumerate(module_specs, start=1)
        ]
        self._session.commit()
        return course, module_rows

    def get_course(self, course_id: str) -> CourseRecord | None:
        return self._session.get(CourseRecord, course_id)

    def update_progress(self, course_id: str, module_id: str, completion_percent: float, assessment_score: float | None) -> LearningProgressRecord:
        course = self._session.get(CourseRecord, course_id)
        if course is None:
            raise NotFoundError("Course not found", {"course_id": course_id})
        module = self._session.get(CourseModuleRecord, module_id)
        if module is None or module.course_id != course_id:
            raise NotFoundError("Course module not found", {"module_id": module_id})

        progress = self._session.scalar(
            select(LearningProgressRecord).where(
                LearningProgressRecord.course_id == course_id,
                LearningProgressRecord.module_id == module_id,
            )
        )
        if progress is None:
            progress = LearningProgressRecord(
                id=str(uuid4()),
                course_id=course_id,
                module_id=module_id,
                completion_percent=completion_percent,
                assessment_score=assessment_score,
            )
            self._session.add(progress)
        else:
            progress.completion_percent = completion_percent
            progress.assessment_score = assessment_score

        if completion_percent >= 100:
            course.status = "COMPLETED"
        elif completion_percent > 0 and course.status == "GENERATED":
            course.status = "IN_PROGRESS"
        self._session.commit()
        return progress
