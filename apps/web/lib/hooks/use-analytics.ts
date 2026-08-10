import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";

export interface DashboardSummary {
  total_applications: number;
  active_pipeline: number;
  offers: number;
  accepted: number;
  rejected: number;
  withdrawn: number;
  ghosted: number;
  response_rate_pct: number;
  avg_ats_match_score: number | null;
  companies_applied: number;
  status_breakdown: { status: string; count: number }[];
}

export interface SkillDemandItem {
  skill: string;
  category: string;
  job_count: number;
}

export interface DemandAnalytics {
  top_skills: SkillDemandItem[];
  top_companies: { company: string; job_count: number }[];
  skills_by_category: Record<string, SkillDemandItem[]>;
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => apiFetch<DashboardSummary>("/analytics/summary"),
  });
}

export function useDemandAnalytics() {
  return useQuery({
    queryKey: ["analytics", "demand"],
    queryFn: () => apiFetch<DemandAnalytics>("/analytics/demand"),
  });
}
