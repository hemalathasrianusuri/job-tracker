from app.modules.ai.models import InterviewQuestion
from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import InterviewQuestionsResult
from app.modules.jobs.models import Job
from app.modules.resume.models import Resume


class InterviewPrepService:
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    async def generate_and_store(self, *, job: Job, resume: Resume) -> list[InterviewQuestion]:
        result = await self.orchestrator.complete_structured(
            prompt_name="interview",
            variables={
                "company_name": job.company.name if job.company else "the company",
                "job_title": job.title,
                "job_description": job.raw_description or "",
                "resume_text": resume.raw_text or "",
            },
            response_model=InterviewQuestionsResult,
            operation="interview_prep",
        )

        questions = [
            InterviewQuestion(
                job_id=job.id,
                category=item.category,
                question=item.question,
                suggested_answer_notes=item.suggested_answer_notes,
            )
            for item in result.questions
        ]
        self.orchestrator.db.add_all(questions)
        await self.orchestrator.db.flush()
        return questions
