import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";

export interface LearningResource {
  title: string;
  url: string;
  provider: string;
  resource_type: string;
  estimated_hours: number;
  difficulty: string;
}

export interface SkillRoadmapEntry {
  skill: string;
  resources: LearningResource[];
}

export interface LearningRoadmapResult {
  roadmap: SkillRoadmapEntry[];
}

export function useLearningRoadmap(jobId: string | undefined, resumeId: string | undefined) {
  return useQuery({
    queryKey: ["learning", "roadmap", jobId, resumeId],
    queryFn: () => apiFetch<LearningRoadmapResult>(`/learning/roadmap?job_id=${jobId}&resume_id=${resumeId}`),
    enabled: Boolean(jobId && resumeId),
    retry: false, // AI calls that fail (e.g. job hasn't been JD-analyzed yet) shouldn't silently retry 3x
  });
}
