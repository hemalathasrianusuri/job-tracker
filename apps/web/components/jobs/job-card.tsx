"use client";

import { motion } from "framer-motion";
import { MapPin, Star } from "lucide-react";
import { StatusPipeline } from "@/components/jobs/status-pipeline";
import { StatusSelect } from "@/components/jobs/status-select";
import { useUpdateJobStatus } from "@/lib/hooks/use-jobs";
import type { Job, JobStatus } from "@/lib/types/job";

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  if (min && max) return `${fmt(min)}–${fmt(max)}`;
  return fmt((min ?? max)!);
}

export function JobCard({ job }: { job: Job }) {
  const updateStatus = useUpdateJobStatus();
  const salary = formatSalary(job.salary_min, job.salary_max);

  function handleStatusChange(status: JobStatus) {
    updateStatus.mutate({ jobId: job.id, status });
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="group rounded-lg border border-border bg-surface p-4 transition-colors hover:bg-surface-hover"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-display text-sm font-semibold text-foreground">{job.title}</h3>
            {job.referral && <Star className="h-3.5 w-3.5 shrink-0 fill-stage-active text-stage-active" aria-label="Referral" />}
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{job.company?.name ?? "Unknown company"}</p>

          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {job.location}
                {job.work_mode && ` · ${job.work_mode}`}
              </span>
            )}
            {salary && <span className="font-mono tabular-nums">{salary}</span>}
            {job.ats_match_score != null && (
              <span className="font-mono tabular-nums text-stage-active">{job.ats_match_score}% match</span>
            )}
          </div>
        </div>

        <StatusSelect value={job.status} onChange={handleStatusChange} />
      </div>

      <div className="mt-4">
        <StatusPipeline status={job.status} variant="compact" />
      </div>
    </motion.div>
  );
}
