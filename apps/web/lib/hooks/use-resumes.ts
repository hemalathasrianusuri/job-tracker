import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUpload } from "@/lib/api-client";
import type { Resume } from "@/lib/types/resume";

const resumeKeys = { all: ["resumes"] as const };

export function useResumes() {
  return useQuery({
    queryKey: resumeKeys.all,
    queryFn: () => apiFetch<Resume[]>("/resumes"),
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, setAsMaster }: { file: File; setAsMaster: boolean }) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiUpload<Resume>(`/resumes?set_as_master=${setAsMaster}`, formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: resumeKeys.all });
    },
  });
}

export function useDeleteResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resumeId: string) => apiFetch<void>(`/resumes/${resumeId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: resumeKeys.all });
    },
  });
}
