import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string | null;
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isInitializing: boolean; // true until the initial /auth/refresh attempt on app load resolves
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  setInitializing: (value: boolean) => void;
  clear: () => void;
}

// Deliberately in-memory only — no localStorage/sessionStorage. The access
// token disappears on tab close/refresh by design; the httpOnly refresh
// cookie is what survives, and /auth/refresh re-establishes the session.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isInitializing: true,
  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user }),
  setInitializing: (value) => set({ isInitializing: value }),
  clear: () => set({ accessToken: null, user: null }),
}));
