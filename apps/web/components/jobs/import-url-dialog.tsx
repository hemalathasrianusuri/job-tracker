"use client";

import { useState, type FormEvent } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api-client";
import { useQueryClient } from "@tanstack/react-query";
import { jobsQueryKeys } from "@/lib/hooks/use-jobs";

interface ImportUrlDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface DiscoveredJob {
  source: string;
  source_id: string;
  title: string;
  location: string | null;
  url: string;
  raw_description: string;
  company_name: string;
}

export function ImportUrlDialog({ open, onOpenChange }: ImportUrlDialogProps) {
  const [url, setUrl] = useState("");
  const [preview, setPreview] = useState<DiscoveredJob | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleFetch(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsFetching(true);
    try {
      const result = await apiFetch<DiscoveredJob>("/discovery/import-url", {
        method: "POST",
        body: JSON.stringify({ url }),
      });
      setPreview(result);
    } catch {
      setError("Couldn't fetch that page — check the URL and try again.");
    } finally {
      setIsFetching(false);
    }
  }

  async function handleSave() {
    if (!preview) return;
    setIsSaving(true);
    try {
      await apiFetch("/discovery/import", { method: "POST", body: JSON.stringify({ job: preview }) });
      queryClient.invalidateQueries({ queryKey: jobsQueryKeys.all });
      reset();
      onOpenChange(false);
    } catch {
      setError("Couldn't save this job — try again.");
    } finally {
      setIsSaving(false);
    }
  }

  function reset() {
    setUrl("");
    setPreview(null);
    setError(null);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
      title="Import from a job posting URL"
      description="Paste a link to any job posting — we'll pull the text so you can review before saving."
    >
      {!preview ? (
        <form onSubmit={handleFetch} className="space-y-3">
          <Input
            type="url"
            required
            autoFocus
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://boards.greenhouse.io/acme/jobs/12345"
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isFetching}>
              {isFetching ? "Fetching…" : "Fetch"}
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Title</label>
            <Input value={preview.title} onChange={(e) => setPreview({ ...preview, title: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Company</label>
            <Input
              value={preview.company_name}
              onChange={(e) => setPreview({ ...preview, company_name: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Description (extracted)</label>
            <Textarea
              rows={6}
              value={preview.raw_description}
              onChange={(e) => setPreview({ ...preview, raw_description: e.target.value })}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={reset}>
              Back
            </Button>
            <Button type="button" onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving…" : "Save to tracker"}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
