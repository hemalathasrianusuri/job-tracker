"use client";

import { useState } from "react";
import { Plus, Search, Link as LinkIcon } from "lucide-react";
import { AnimatePresence } from "framer-motion";
import { JobCard } from "@/components/jobs/job-card";
import { CreateJobDialog } from "@/components/jobs/create-job-dialog";
import { ImportUrlDialog } from "@/components/jobs/import-url-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useJobs } from "@/lib/hooks/use-jobs";
import { STATUS_LABELS, type JobStatus } from "@/lib/types/job";

const FILTER_TABS: { label: string; status?: JobStatus }[] = [
  { label: "All" },
  { label: STATUS_LABELS.wishlist, status: "wishlist" },
  { label: STATUS_LABELS.applied, status: "applied" },
  { label: STATUS_LABELS.interview_1, status: "interview_1" },
  { label: STATUS_LABELS.offer, status: "offer" },
  { label: STATUS_LABELS.rejected, status: "rejected" },
];

export default function JobsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<JobStatus | undefined>(undefined);
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);

  const { data, isLoading, isError } = useJobs({ status: statusFilter, search: search || undefined });

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-foreground">Jobs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data ? `${data.total} application${data.total === 1 ? "" : "s"} tracked` : "Loading your pipeline…"}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          Log application
        </Button>
      </div>

      <div className="mt-3 flex justify-end">
        <button
          onClick={() => setImportOpen(true)}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          <LinkIcon className="h-3 w-3" />
          Or import from a posting URL
        </button>
      </div>

      <div className="mt-6 flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by role…"
            className="pl-8"
          />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-1 border-b border-border">
        {FILTER_TABS.map((tab) => {
          const isActive = statusFilter === tab.status;
          return (
            <button
              key={tab.label}
              onClick={() => setStatusFilter(tab.status)}
              className={`relative px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
              {isActive && <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-primary" />}
            </button>
          );
        })}
      </div>

      <div className="mt-6 space-y-3">
        {isLoading && (
          <div className="py-16 text-center text-sm text-muted-foreground">Loading applications…</div>
        )}

        {isError && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            Couldn't load your applications. Try refreshing the page.
          </div>
        )}

        {data && data.items.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-16 text-center">
            <p className="font-display text-sm font-medium text-foreground">Nothing here yet</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Log your first application to start tracking it through the pipeline.
            </p>
            <Button className="mt-4" size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-3.5 w-3.5" />
              Log application
            </Button>
          </div>
        )}

        <AnimatePresence initial={false}>
          {data?.items.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </AnimatePresence>
      </div>

      <CreateJobDialog open={createOpen} onOpenChange={setCreateOpen} />
      <ImportUrlDialog open={importOpen} onOpenChange={setImportOpen} />
    </div>
  );
}
