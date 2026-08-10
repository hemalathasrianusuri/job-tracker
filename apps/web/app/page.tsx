"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function RootPage() {
  const router = useRouter();
  const isInitializing = useAuthStore((s) => s.isInitializing);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (isInitializing) return;
    router.replace(user ? "/dashboard" : "/login");
  }, [isInitializing, user, router]);

  return null;
}
