import { useAuthStore } from "@/lib/stores/auth-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let refreshPromise: Promise<string | null> | null = null;

/**
 * Calls POST /auth/refresh. The refresh token itself is an httpOnly cookie —
 * this fetch never sees it, it just relies on `credentials: "include"` to send it.
 * De-duped via a shared in-flight promise so concurrent 401s don't trigger a
 * refresh stampede.
 */
async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const data = await res.json();
        useAuthStore.getState().setAccessToken(data.access_token);
        return data.access_token as string;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface RequestOptions extends RequestInit {
  skipAuthRetry?: boolean;
}

/**
 * Core fetch wrapper: attaches the in-memory access token, and on a 401
 * transparently refreshes once and retries. If refresh also fails, it clears
 * auth state so the UI can redirect to /login.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const accessToken = useAuthStore.getState().accessToken;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  });

  if (res.status === 401 && !options.skipAuthRetry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return apiFetch<T>(path, { ...options, skipAuthRetry: true });
    }
    useAuthStore.getState().clear();
    throw new ApiError(401, "Session expired — please log in again");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Request failed");
  }

  // 204 No Content (e.g. logout) has no body to parse
  if (res.status === 204) return undefined as T;
  return res.json();
}

/**
 * Multipart upload variant of apiFetch. Deliberately does NOT set
 * Content-Type — the browser sets it automatically with the correct
 * multipart boundary when the body is a FormData instance; setting it
 * manually breaks the boundary and the server can't parse the body.
 */
export async function apiUpload<T>(path: string, formData: FormData, options: RequestOptions = {}): Promise<T> {
  const accessToken = useAuthStore.getState().accessToken;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    ...options,
    credentials: "include",
    headers: {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
    body: formData,
  });

  if (res.status === 401 && !options.skipAuthRetry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return apiUpload<T>(path, formData, { ...options, skipAuthRetry: true });
    }
    useAuthStore.getState().clear();
    throw new ApiError(401, "Session expired — please log in again");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Upload failed");
  }

  return res.json();
}

export const authApi = {
  register: (email: string, password: string, fullName?: string) =>
    apiFetch<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => apiFetch<void>("/auth/logout", { method: "POST" }),
  me: () => apiFetch<{ id: string; email: string; full_name: string | null }>("/auth/me"),
  googleLoginUrl: () => `${API_BASE_URL}/auth/google/login`,
};
