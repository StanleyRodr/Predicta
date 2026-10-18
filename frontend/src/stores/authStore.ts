import { create } from "zustand";
import type { User } from "../types/api";

const TOKEN_KEY = "predicta_access_token";

interface AuthState {
  token: string | null;
  user: User | null;
  isHydrated: boolean;
  setSession: (token: string, user: User | null) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isHydrated: false,
  setSession: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, user, isHydrated: true });
  },
  setUser: (user) => set({ user }),
  clearSession: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, user: null, isHydrated: true });
  },
  hydrate: () => {
    set({ token: localStorage.getItem(TOKEN_KEY), isHydrated: true });
  },
}));

export { TOKEN_KEY };
