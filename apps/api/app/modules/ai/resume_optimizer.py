from app.modules.ai.orchestrator import AIOrchestrator
from app.modules.ai.schemas import AtsScoreResult
from app.modules.jobs.models import Job
from app.modules.resume.models import Resume


class ResumeOptimizerService:
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator

    async def score(self, *, job: Job, resume: Resume) -> AtsScoreResult:
        if not job.raw_description:
            raise ValueError("Job has no description to score against")
        if not resume.raw_text:
            raise ValueError("Resume has no extracted text to score")

        result = await self.orchestrator.complete_structured(
            prompt_name="ats",
            variables={"job_description": job.raw_description, "resume_text": resume.raw_text},
            response_model=AtsScoreResult,
            operation="ats_score",
            # Not cached: re-scoring after the person edits their resume should
            # always hit the model, not return a stale score from before the edit.
            use_cache=False,
        )

        # Both records get the score — resume.ats_score is the resume's general
        # quality baseline, job.ats_match_score is specific to this pairing.
        resume.ats_score = result.ats_score
        job.ats_match_score = result.ats_score
        return result
