from pydantic import BaseModel, Field


class JDAnalysisResult(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    cloud_platforms: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    devops_tools: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    min_experience_years: float | None = None
    education_requirement: str | None = None
    key_responsibilities: list[str] = Field(default_factory=list)
    difficulty_score: float = Field(ge=1, le=10)
    seniority_level: str


class MissingSkill(BaseModel):
    skill: str
    priority_score: float = Field(ge=1, le=10)
    impact_score: float = Field(ge=1, le=10)
    learning_difficulty: str
    estimated_learning_hours: float


class SkillGapResult(BaseModel):
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    weak_skills: list[str] = Field(default_factory=list)
    unused_experience: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    overall_match_percentage: float = Field(ge=0, le=100)


class ScoreBreakdown(BaseModel):
    keyword_match: float = Field(ge=0, le=100)
    formatting: float = Field(ge=0, le=100)
    quantified_achievements: float = Field(ge=0, le=100)


class WeakBullet(BaseModel):
    original: str
    rewritten: str
    reason: str


class AtsScoreResult(BaseModel):
    ats_score: float = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    strong_bullets: list[str] = Field(default_factory=list)
    weak_bullets: list[WeakBullet] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class CoverLetterResult(BaseModel):
    subject_line: str
    body: str


class InterviewQuestionItem(BaseModel):
    category: str
    question: str
    suggested_answer_notes: str


class InterviewQuestionsResult(BaseModel):
    questions: list[InterviewQuestionItem]


class ExtractedSkill(BaseModel):
    name: str
    category: str
    proficiency: str


class ResumeSkillExtractionResult(BaseModel):
    skills: list[ExtractedSkill] = Field(default_factory=list)
