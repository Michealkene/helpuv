import { useAuthStore } from '@/store/authStore'

export function useAuth() {
  const { user, setAuth, logout } = useAuthStore()
  
  return {
    user,
    isAuthenticated: !!user,
    login: setAuth,
    logout,
  }
}