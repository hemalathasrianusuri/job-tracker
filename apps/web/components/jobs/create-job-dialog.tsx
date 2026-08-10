"use client";

import { useState, type FormEvent } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useCreateJob } from "@/lib/hooks/use-jobs";
import type { WorkMode } from "@/lib/types/job";

interface CreateJobDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const initialFormState = {
  company_name: "",
  title: "",
  location: "",
  work_mode: "" as WorkMode | "",
  salary_min: "",
  salary_max: "",
  source_url: "",
  raw_description: "",
  referral: false,
};

export function CreateJobDialog({ open, onOpenChange }: CreateJobDialogProps) {
  const [form, setForm] = useState(initialFormState);
  const createJob = useCreateJob();

  function update<K extends keyof typeof initialFormState>(key: K, value: (typeof initialFormState)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await createJob.mutateAsync({
      company_name: form.company_name,
      title: form.title,
      location: form.location || undefined,
      work_mode: form.work_mode || undefined,
      salary_min: form.salary_min ? Number(form.salary_min) : undefined,
      salary_max: form.salary_max ? Number(form.salary_max) : undefined,
      source_url: form.source_url || undefined,
      raw_description: form.raw_description || undefined,
      referral: form.referral,
    });
    setForm(initialFormState);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Log an application" description="Add a role to your tracker.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Company</label>
            <Input
              required
              value={form.company_name}
              onChange={(e) => update("company_name", e.target.value)}
              placeholder="Stripe"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Role</label>
            <Input
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="Backend Engineer"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Location</label>
            <Input value={form.location} onChange={(e) => update("location", e.target.value)} placeholder="Remote" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Work mode</label>
            <select
              value={form.work_mode}
              onChange={(e) => update("work_mode", e.target.value as WorkMode | "")}
              className="flex h-9 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">—</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Salary min</label>
            <Input
              type="number"
              value={form.salary_min}
              onChange={(e) => update("salary_min", e.target.value)}
              placeholder="120000"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Salary max</label>
            <Input
              type="number"
              value={form.salary_max}
              onChange={(e) => update("salary_max", e.target.value)}
              placeholder="160000"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Job posting URL</label>
          <Input
            type="url"
            value={form.source_url}
            onChange={(e) => update("source_url", e.target.value)}
            placeholder="https://..."
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">
            Job description <span className="text-muted-foreground/60">(paste it in to unlock AI analysis, skill-gap, and ATS scoring)</span>
          </label>
          <Textarea
            rows={5}
            value={form.raw_description}
            onChange={(e) => update("raw_description", e.target.value)}
            placeholder="Paste the full job description here…"
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={form.referral}
            onChange={(e) => update("referral", e.target.checked)}
            className="h-4 w-4 rounded border-border bg-surface accent-primary"
          />
          I have a referral
        </label>

        {createJob.isError && (
          <p className="text-sm text-destructive">Couldn't save this — check the fields and try again.</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="submit" disabled={createJob.isPending}>
            {createJob.isPending ? "Saving…" : "Add application"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
