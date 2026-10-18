import { create } from "zustand";
import type { User } from "../types/api";

const TOKEN_KEY = "predicta_access_token";

interface AuthState {
  token: string | null;
  user: User | null;
  isHydrated: boolean;
  isCheckingSession: boolean;
  setSession: (token: string, user: User | null) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isHydrated: false,
  isCheckingSession: false,
  setSession: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, user, isHydrated: true, isCheckingSession: user === null });
  },
  setUser: (user) => set({ user, isCheckingSession: false }),
  clearSession: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, user: null, isHydrated: true, isCheckingSession: false });
  },
  hydrate: () => {
    const token = localStorage.getItem(TOKEN_KEY);
    set({ token, isHydrated: true, isCheckingSession: token !== null });
  },
}));

export { TOKEN_KEY };
