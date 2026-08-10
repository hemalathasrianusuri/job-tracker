import { ACTIVE_PIPELINE, TERMINAL_STATUSES, STATUS_LABELS, type JobStatus } from "@/lib/types/job";
import { cn } from "@/lib/utils";

const TIER_COLOR = {
  0: "bg-stage-idle",
  1: "bg-stage-active",
  2: "bg-stage-active-deep",
} as const;

const TIER_RING = {
  0: "ring-stage-idle/40",
  1: "ring-stage-active/40",
  2: "ring-stage-active-deep/40",
} as const;

interface StatusPipelineProps {
  status: JobStatus;
  /** Compact renders as a small inline rail for job cards; full renders with labels, for the job detail view. */
  variant?: "compact" | "full";
  className?: string;
}

export function StatusPipeline({ status, variant = "compact", className }: StatusPipelineProps) {
  const terminal = TERMINAL_STATUSES[status];

  if (terminal) {
    const dotClass =
      terminal.kind === "success"
        ? "bg-stage-success"
        : terminal.kind === "danger"
          ? "bg-stage-danger"
          : "bg-muted-foreground";
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <span className={cn("h-2 w-2 rounded-full", dotClass)} />
        <span className="text-xs font-medium text-muted-foreground">{terminal.label}</span>
      </div>
    );
  }

  const currentIndex = ACTIVE_PIPELINE.findIndex((stage) => stage.status === status);

  return (
    <div className={cn("flex items-center gap-1", className)} role="img" aria-label={`Pipeline stage: ${STATUS_LABELS[status]}`}>
      {ACTIVE_PIPELINE.map((stage, i) => {
        const isPast = i < currentIndex;
        const isCurrent = i === currentIndex;
        const isFuture = i > currentIndex;

        return (
          <div key={stage.status} className="group relative flex items-center">
            <div
              className={cn(
                "rounded-full transition-all",
                variant === "compact" ? "h-1.5 w-1.5" : "h-2.5 w-2.5",
                isFuture ? "bg-border" : TIER_COLOR[stage.tier],
                isCurrent && variant === "full" && `ring-2 ${TIER_RING[stage.tier]} ring-offset-2 ring-offset-surface`,
                isPast && "opacity-60"
              )}
            />
            {i < ACTIVE_PIPELINE.length - 1 && (
              <div
                className={cn(
                  "transition-colors",
                  variant === "compact" ? "h-px w-2" : "h-px w-4",
                  isFuture ? "bg-border" : "bg-stage-active/50"
                )}
              />
            )}
            {variant === "full" && (
              <span
                className={cn(
                  "absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px]",
                  isCurrent ? "font-medium text-foreground" : "text-muted-foreground"
                )}
              >
                {stage.label}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
