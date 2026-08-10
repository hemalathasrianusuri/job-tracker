"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";

/**
 * The backend redirects here after a successful Google OAuth flow with the
 * access token in the URL FRAGMENT (#access_token=...), not a query param —
 * fragments are never sent to the server in the redirect request or logged
 * in server access logs, only readable by client-side JS. The refresh token
 * cookie is already set by the backend's redirect response by this point.
 */
export default function OAuthCallbackPage() {
  const router = useRouter();
  const setAccessToken = useAuthStore((s) => s.setAccessToken);

  useEffect(() => {
    const fragment = window.location.hash;
    const params = new URLSearchParams(fragment.replace("#", ""));
    const accessToken = params.get("access_token");

    if (accessToken) {
      setAccessToken(accessToken);
      // Strip the token from the URL immediately so it doesn't linger in
      // browser history.
      window.history.replaceState(null, "", window.location.pathname);
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router, setAccessToken]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-sm text-muted-foreground">Signing you in…</p>
    </div>
  );
}
