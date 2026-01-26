import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
}

interface AuthState {
  user: User | null;
  access_token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      access_token: null,
      setAuth: (user, token) => {
        localStorage.setItem('access_token', token);
        set({ user, access_token: token });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, access_token: null });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);