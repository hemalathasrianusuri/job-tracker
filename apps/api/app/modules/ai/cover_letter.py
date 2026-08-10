from app.modules.ai.models import GeneratedDocument
from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import CoverLetterResult
from app.modules.jobs.models import Job
from app.modules.resume.models import Resume


class CoverLetterService:
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    async def generate_and_store(self, *, job: Job, resume: Resume, tone: str = "professional") -> GeneratedDocument:
        if not resume.raw_text:
            raise ValueError("Resume has no extracted text to draw from")

        result = await self.orchestrator.complete_structured(
            prompt_name="cover_letter",
            variables={
                "company_name": job.company.name if job.company else "the company",
                "job_title": job.title,
                "job_description": job.raw_description or "",
                "resume_text": resume.raw_text,
                "tone": tone,
            },
            response_model=CoverLetterResult,
            operation="cover_letter",
            # Cover letters are personalized per generation request (tone can
            # vary) — caching would silently ignore a tone change.
            use_cache=False,
        )

        document = GeneratedDocument(
            job_id=job.id,
            doc_type="cover_letter",
            content=result.body,
            model_used=self.orchestrator.primary.name,
        )
        self.orchestrator.db.add(document)
        await self.orchestrator.db.flush()
        await self.orchestrator.db.refresh(document)
        return document
