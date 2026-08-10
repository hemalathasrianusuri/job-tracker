"use client";

import { ResumeUploader } from "@/components/resume/resume-uploader";
import { ResumeListItem } from "@/components/resume/resume-list-item";
import { useResumes } from "@/lib/hooks/use-resumes";

export default function ResumePage() {
  const { data: resumes, isLoading } = useResumes();

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-foreground">Resume</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Upload versions of your resume to score against jobs and generate tailored documents.
      </p>

      <div className="mt-6">
        <ResumeUploader />
      </div>

      <div className="mt-6 space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {resumes?.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">No resumes uploaded yet.</p>
        )}
        {resumes?.map((resume) => (
          <ResumeListItem key={resume.id} resume={resume} />
        ))}
      </div>
    </div>
  );
}
