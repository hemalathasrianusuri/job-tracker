"use client";

import { FileText, Star, Trash2 } from "lucide-react";
import { useDeleteResume } from "@/lib/hooks/use-resumes";
import type { Resume } from "@/lib/types/resume";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function ResumeListItem({ resume }: { resume: Resume }) {
  const deleteResume = useDeleteResume();

  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border bg-surface p-4">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-surface-hover">
          <FileText className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="truncate text-sm font-medium text-foreground">{resume.original_filename}</p>
            {resume.is_master && (
              <span title="Master resume">
                <Star className="h-3.5 w-3.5 fill-stage-active text-stage-active" />
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            Uploaded {formatDate(resume.created_at)}
            {resume.ats_score != null && ` · ${resume.ats_score}% ATS baseline`}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <a
          href={resume.file_url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-surface-hover hover:text-foreground"
        >
          View
        </a>
        <button
          onClick={() => deleteResume.mutate(resume.id)}
          disabled={deleteResume.isPending}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
          aria-label="Delete resume"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
