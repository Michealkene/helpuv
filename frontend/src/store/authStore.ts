import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/lib/api'
import type { User, AdminUser, AuthResponse, AdminAuthResponse } from '@/types'

interface AuthState {
  // User auth
  user: User | null
  isAuthenticated: boolean

  // Admin auth
  admin: AdminUser | null
  isAdminAuthenticated: boolean

  // Actions
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  googleLogin: (credential: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>

  // Admin actions
  adminLogin: (email: string, password: string) => Promise<void>
  adminLogout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      admin: null,
      isAdminAuthenticated: false,
      
      // User login
      login: async (email: string, password: string) => {
        const response = await api.post<AuthResponse>('/auth/login', {
          email,
          password,
        })
        
        const { access_token, refresh_token, user } = response.data
        
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        
        set({ user, isAuthenticated: true })
      },
      
      // User signup
      signup: async (email: string, password: string, name: string) => {
        const response = await api.post<AuthResponse>('/auth/signup', {
          email,
          password,
          name,
        })

        const { access_token, refresh_token, user } = response.data

        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)

        set({ user, isAuthenticated: true })
      },

      // Google OAuth login
      googleLogin: async (credential: string) => {
        const response = await api.post<AuthResponse>('/auth/google', {
          credential,
        })

        const { access_token, refresh_token, user } = response.data

        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)

        set({ user, isAuthenticated: true })
      },

      // User logout
      logout: () => {
        const refreshToken = localStorage.getItem('refresh_token')
        
        // Try to revoke token on server
        if (refreshToken) {
          api.post('/auth/logout', { refresh_token: refreshToken }).catch(() => {})
        }
        
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        
        set({ user: null, isAuthenticated: false })
      },
      
      // Check authentication status
      checkAuth: async () => {
        const token = localStorage.getItem('access_token')
        
        if (!token) {
          set({ user: null, isAuthenticated: false })
          return
        }
        
        try {
          const response = await api.get<User>('/auth/me')
          set({ user: response.data, isAuthenticated: true })
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, isAuthenticated: false })
        }
      },
      
      // Admin login
      adminLogin: async (email: string, password: string) => {
        const response = await api.post<AdminAuthResponse>('/admin/login', {
          email,
          password,
        })
        
        const { access_token, admin } = response.data
        
        localStorage.setItem('admin_token', access_token)
        
        set({ admin, isAdminAuthenticated: true })
      },
      
      // Admin logout
      adminLogout: () => {
        localStorage.removeItem('admin_token')
        set({ admin: null, isAdminAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        admin: state.admin,
        isAdminAuthenticated: state.isAdminAuthenticated,
      }),
    }
  )
)
