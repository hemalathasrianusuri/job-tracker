"use client";

import { useState } from "react";
import { BookOpen, ExternalLink } from "lucide-react";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useResumes } from "@/lib/hooks/use-resumes";
import { useLearningRoadmap } from "@/lib/hooks/use-learning";

const DIFFICULTY_COLOR: Record<string, string> = {
  beginner: "text-stage-success",
  intermediate: "text-stage-active",
  advanced: "text-stage-danger",
};

export default function LearningPage() {
  const { data: jobsData } = useJobs({ pageSize: 100 });
  const { data: resumes } = useResumes();

  const [jobId, setJobId] = useState<string>("");
  const [resumeId, setResumeId] = useState<string>("");

  const { data: roadmap, isFetching, isError, error } = useLearningRoadmap(
    jobId || undefined,
    resumeId || undefined
  );

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-foreground">Learning Roadmap</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Free resources for the skill gap between your resume and a specific job.
      </p>

      <div className="mt-6 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Job</label>
          <select
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            className="h-9 min-w-[220px] rounded-md border border-border bg-surface px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select a job…</option>
            {jobsData?.items.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} — {job.company?.name ?? "Unknown"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Resume</label>
          <select
            value={resumeId}
            onChange={(e) => setResumeId(e.target.value)}
            className="h-9 min-w-[220px] rounded-md border border-border bg-surface px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select a resume…</option>
            {resumes?.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.original_filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!jobId || !resumeId ? (
        <div className="mt-10 flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-14 text-center">
          <BookOpen className="h-6 w-6 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">Pick a job and a resume to generate a roadmap.</p>
        </div>
      ) : isFetching ? (
        <div className="mt-10 text-center text-sm text-muted-foreground">Building your roadmap…</div>
      ) : isError ? (
        <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          Couldn't generate a roadmap — make sure this job has been AI-analyzed first
          (<code className="font-mono text-xs">POST /ai/jobs/{"{job_id}"}/analyze</code>), then try again.
        </div>
      ) : roadmap && roadmap.roadmap.length === 0 ? (
        <div className="mt-10 text-center text-sm text-muted-foreground">
          No skill gaps found — this resume already covers what the job asks for.
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {roadmap?.roadmap.map((entry) => (
            <div key={entry.skill} className="rounded-lg border border-border bg-surface p-4">
              <h3 className="font-display text-sm font-semibold text-foreground">{entry.skill}</h3>
              <div className="mt-3 space-y-2">
                {entry.resources.map((resource, i) => (
                  <a
                    key={i}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm hover:bg-surface-hover"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-foreground">{resource.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {resource.provider} · {resource.resource_type} · {resource.estimated_hours}h ·{" "}
                        <span className={DIFFICULTY_COLOR[resource.difficulty] ?? ""}>{resource.difficulty}</span>
                      </p>
                    </div>
                    <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
