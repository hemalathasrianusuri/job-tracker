from pydantic import BaseModel


class LearningResource(BaseModel):
    title: str
    url: str
    provider: str
    resource_type: str
    estimated_hours: float
    difficulty: str


class SkillRoadmapEntry(BaseModel):
    skill: str
    resources: list[LearningResource]


class LearningRoadmapResult(BaseModel):
    roadmap: list[SkillRoadmapEntry]
