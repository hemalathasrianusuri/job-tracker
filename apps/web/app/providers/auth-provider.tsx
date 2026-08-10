"use client";

import { useEffect, type ReactNode } from "react";
import { authApi, apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/lib/stores/auth-store";

/**
 * Mount once in the root layout. On every hard page load the in-memory
 * access token is gone (by design — see auth-store.ts), so this silently
 * calls /auth/refresh using the httpOnly cookie to get a fresh access token
 * before rendering anything that needs auth.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const setInitializing = useAuthStore((s) => s.setInitializing);
  const clear = useAuthStore((s) => s.clear);

  useEffect(() => {
    async function hydrateSession() {
      try {
        const { access_token } = await apiFetch<{ access_token: string }>("/auth/refresh", {
          method: "POST",
          skipAuthRetry: true,
        });
        setAccessToken(access_token);
        const user = await authApi.me();
        setUser(user);
      } catch {
        clear(); // no valid session — user will hit the login page via middleware
      } finally {
        setInitializing(false);
      }
    }
    hydrateSession();
  }, [setAccessToken, setUser, setInitializing, clear]);

  return <>{children}</>;
}
