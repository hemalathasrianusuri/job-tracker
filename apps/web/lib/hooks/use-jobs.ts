import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import type { Job, JobStatus, PaginatedJobs } from "@/lib/types/job";
import type { CreateJobPayload } from "@/lib/types/requests";

export const jobsQueryKeys = {
  all: ["jobs"] as const,
  list: (filters: JobListFilters) => [...jobsQueryKeys.all, "list", filters] as const,
  detail: (id: string) => [...jobsQueryKeys.all, "detail", id] as const,
};

export interface JobListFilters {
  status?: JobStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

function buildQueryString(filters: JobListFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.search) params.set("search", filters.search);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 50));
  return params.toString();
}

export function useJobs(filters: JobListFilters = {}) {
  return useQuery({
    queryKey: jobsQueryKeys.list(filters),
    queryFn: () => apiFetch<PaginatedJobs>(`/jobs?${buildQueryString(filters)}`),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateJobPayload) =>
      apiFetch<Job>("/jobs", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobsQueryKeys.all });
    },
  });
}

export function useUpdateJobStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, status, notes }: { jobId: string; status: JobStatus; notes?: string }) =>
      apiFetch<Job>(`/jobs/${jobId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status, notes }),
      }),
    // Optimistic update: the pipeline rail should react instantly on drag/click,
    // not wait a round trip — this is a UI the person will use dozens of times
    // a day, so perceived latency matters more than most CRUD screens.
    onMutate: async ({ jobId, status }) => {
      await queryClient.cancelQueries({ queryKey: jobsQueryKeys.all });
      const previous = queryClient.getQueriesData<PaginatedJobs>({ queryKey: jobsQueryKeys.all });

      queryClient.setQueriesData<PaginatedJobs>({ queryKey: jobsQueryKeys.all }, (old) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((job) => (job.id === jobId ? { ...job, status } : job)),
        };
      });

      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data);
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: jobsQueryKeys.all });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => apiFetch<void>(`/jobs/${jobId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobsQueryKeys.all });
    },
  });
}
