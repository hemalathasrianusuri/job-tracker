import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        neutral: "bg-surface-hover text-muted-foreground border border-border",
        idle: "bg-stage-idle/15 text-stage-idle",
        active: "bg-stage-active/15 text-stage-active",
        deep: "bg-stage-active-deep/15 text-stage-active-deep",
        success: "bg-stage-success/15 text-stage-success",
        danger: "bg-stage-danger/15 text-stage-danger",
      },
    },
    defaultVariants: { variant: "neutral" },
  }
);

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
