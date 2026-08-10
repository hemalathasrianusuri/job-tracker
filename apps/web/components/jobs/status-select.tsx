"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import { ACTIVE_PIPELINE, TERMINAL_STATUSES, STATUS_LABELS, type JobStatus } from "@/lib/types/job";
import { cn } from "@/lib/utils";

interface StatusSelectProps {
  value: JobStatus;
  onChange: (status: JobStatus) => void;
}

const ALL_STATUSES: JobStatus[] = [
  ...ACTIVE_PIPELINE.map((s) => s.status),
  "offer",
  "accepted",
  "rejected",
  "withdrawn",
  "ghosted",
];

export function StatusSelect({ value, onChange }: StatusSelectProps) {
  return (
    <Select.Root value={value} onValueChange={(v) => onChange(v as JobStatus)}>
      <Select.Trigger className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 text-xs font-medium text-foreground outline-none hover:bg-surface-hover focus-visible:ring-2 focus-visible:ring-ring">
        <Select.Value>{STATUS_LABELS[value]}</Select.Value>
        <Select.Icon>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="z-50 overflow-hidden rounded-md border border-border bg-surface shadow-elevated">
          <Select.Viewport className="p-1">
            {ALL_STATUSES.map((status) => {
              const terminal = TERMINAL_STATUSES[status];
              return (
                <Select.Item
                  key={status}
                  value={status}
                  className={cn(
                    "flex cursor-pointer select-none items-center justify-between rounded-sm px-2 py-1.5 text-xs outline-none",
                    "text-foreground hover:bg-surface-hover data-[highlighted]:bg-surface-hover",
                    terminal?.kind === "danger" && "text-stage-danger",
                    terminal?.kind === "success" && "text-stage-success"
                  )}
                >
                  <Select.ItemText>{STATUS_LABELS[status]}</Select.ItemText>
                  <Select.ItemIndicator>
                    <Check className="h-3.5 w-3.5" />
                  </Select.ItemIndicator>
                </Select.Item>
              );
            })}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
