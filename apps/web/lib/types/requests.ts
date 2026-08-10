import { WorkMode, JobStatus } from "./job";

export interface CreateJobPayload {
  company_name: string;
  title: string;
  location?: string;
  work_mode?: WorkMode;
  salary_min?: number;
  salary_max?: number;
  source_url?: string;
  raw_description?: string;
  referral?: boolean;
  recruiter_name?: string;
  status?: JobStatus;
}
