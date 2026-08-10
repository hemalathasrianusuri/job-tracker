export type JobStatus =
  | "wishlist"
  | "applied"
  | "oa_scheduled"
  | "oa_completed"
  | "interview_1"
  | "interview_2"
  | "interview_3"
  | "hr_round"
  | "offer"
  | "accepted"
  | "rejected"
  | "withdrawn"
  | "ghosted";

export type WorkMode = "remote" | "hybrid" | "onsite";

export interface Company {
  id: string;
  name: string;
  domain: string | null;
  logo_url: string | null;
  industry: string | null;
}

export interface Job {
  id: string;
  company: Company | null;
  title: string;
  location: string | null;
  work_mode: WorkMode | null;
  salary_min: number | null;
  salary_max: number | null;
  source_url: string | null;
  status: JobStatus;
  referral: boolean;
  recruiter_name: string | null;
  applied_at: string | null;
  ats_match_score: number | null;
  resume_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedJobs {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * The active (non-terminal) pipeline in order — this ordering IS the signature
 * visual element (see components/jobs/status-pipeline.tsx). "tier" drives
 * color intensity: higher tier = deeper into the funnel = more saturated.
 */
export const ACTIVE_PIPELINE: { status: JobStatus; label: string; tier: 0 | 1 | 2 }[] = [
  { status: "wishlist", label: "Wishlist", tier: 0 },
  { status: "applied", label: "Applied", tier: 1 },
  { status: "oa_scheduled", label: "OA Scheduled", tier: 1 },
  { status: "oa_completed", label: "OA Completed", tier: 1 },
  { status: "interview_1", label: "Interview 1", tier: 2 },
  { status: "interview_2", label: "Interview 2", tier: 2 },
  { status: "interview_3", label: "Interview 3", tier: 2 },
  { status: "hr_round", label: "HR Round", tier: 2 },
];

export const TERMINAL_STATUSES: Record<JobStatus, { label: string; kind: "success" | "danger" | "neutral" } | undefined> = {
  wishlist: undefined,
  applied: undefined,
  oa_scheduled: undefined,
  oa_completed: undefined,
  interview_1: undefined,
  interview_2: undefined,
  interview_3: undefined,
  hr_round: undefined,
  offer: { label: "Offer", kind: "success" },
  accepted: { label: "Accepted", kind: "success" },
  rejected: { label: "Rejected", kind: "danger" },
  withdrawn: { label: "Withdrawn", kind: "neutral" },
  ghosted: { label: "Ghosted", kind: "neutral" },
};

export const STATUS_LABELS: Record<JobStatus, string> = {
  wishlist: "Wishlist",
  applied: "Applied",
  oa_scheduled: "OA Scheduled",
  oa_completed: "OA Completed",
  interview_1: "Interview 1",
  interview_2: "Interview 2",
  interview_3: "Interview 3",
  hr_round: "HR Round",
  offer: "Offer",
  accepted: "Accepted",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  ghosted: "Ghosted",
};
