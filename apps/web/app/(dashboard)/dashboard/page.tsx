"use client";

import Link from "next/link";
import { useDashboardSummary, useDemandAnalytics } from "@/lib/hooks/use-analytics";
import { ACTIVE_PIPELINE } from "@/lib/types/job";
import { cn } from "@/lib/utils";

function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: "success" | "danger" }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1.5 font-mono text-2xl font-medium tabular-nums",
          accent === "success" && "text-stage-success",
          accent === "danger" && "text-stage-danger",
          !accent && "text-foreground"
        )}
      >
        {value}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: demand } = useDemandAnalytics();

  const statusCounts = new Map((summary?.status_breakdown ?? []).map((s) => [s.status, s.count]));
  const maxFunnelCount = Math.max(1, ...ACTIVE_PIPELINE.map((s) => statusCounts.get(s.status) ?? 0));

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-foreground">Dashboard</h1>
      <p className="mt-1 text-sm text-muted-foreground">Where your search stands right now.</p>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Active pipeline" value={isLoading ? "—" : summary!.active_pipeline} />
        <StatCard label="Response rate" value={isLoading ? "—" : `${summary!.response_rate_pct}%`} />
        <StatCard label="Offers" value={isLoading ? "—" : summary!.offers} accent="success" />
        <StatCard label="Rejected" value={isLoading ? "—" : summary!.rejected} accent="danger" />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatCard label="Avg ATS match" value={isLoading ? "—" : summary?.avg_ats_match_score != null ? `${summary.avg_ats_match_score}%` : "—"} />
        <StatCard label="Companies applied" value={isLoading ? "—" : summary!.companies_applied} />
        <StatCard label="Total tracked" value={isLoading ? "—" : summary!.total_applications} />
      </div>

      {/* Funnel — same pipeline data model and color scale as the job card rail. */}
      <div className="mt-8 rounded-lg border border-border bg-surface p-6">
        <h2 className="font-display text-sm font-semibold text-foreground">Pipeline funnel</h2>
        <div className="mt-5 space-y-2.5">
          {ACTIVE_PIPELINE.map((stage) => {
            const count = statusCounts.get(stage.status) ?? 0;
            const widthPct = Math.max(4, (count / maxFunnelCount) * 100);
            const barColor =
              stage.tier === 0 ? "bg-stage-idle" : stage.tier === 1 ? "bg-stage-active" : "bg-stage-active-deep";
            return (
              <div key={stage.status} className="flex items-center gap-3">
                <span className="w-24 shrink-0 text-xs text-muted-foreground">{stage.label}</span>
                <div className="h-6 flex-1 overflow-hidden rounded bg-background">
                  <div className={cn("h-full rounded transition-all", barColor)} style={{ width: `${widthPct}%` }} />
                </div>
                <span className="w-6 shrink-0 text-right font-mono text-xs tabular-nums text-foreground">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Demand analytics — top skills across the user's own saved jobs,
          populated by the Phase 5 JD analyzer via job_skills. */}
      {demand && demand.top_skills.length > 0 && (
        <div className="mt-6 rounded-lg border border-border bg-surface p-6">
          <h2 className="font-display text-sm font-semibold text-foreground">Most in-demand skills in your search</h2>
          <p className="mt-1 text-xs text-muted-foreground">Across the jobs you've analyzed with AI.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {demand.top_skills.slice(0, 20).map((item) => (
              <span
                key={item.skill}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-foreground"
              >
                {item.skill}
                <span className="font-mono text-muted-foreground">{item.job_count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {!isLoading && summary?.total_applications === 0 && (
        <div className="mt-8 flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-14 text-center">
          <p className="font-display text-sm font-medium text-foreground">Your dashboard is waiting on data</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Log your first application and this fills in on its own.
          </p>
          <Link href="/jobs" className="mt-4 text-sm font-medium text-primary hover:underline">
            Go to Jobs →
          </Link>
        </div>
      )}
    </div>
  );
}
