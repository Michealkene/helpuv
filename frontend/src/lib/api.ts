// frontend/src/lib/api.ts
import axios from 'axios'

// CRITICAL FIX: Use relative path to go through Nginx
// In Docker/production: requests go to Nginx on port 80
// Nginx routes /api/* to backend container
const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

console.log('🔧 API Base URL:', API_URL) // Debug log

// Create axios instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // Increased to 30 seconds
})

// Add request interceptor to attach auth token
api.interceptors.request.use(
  (config) => {
    console.log('📤 API Request:', config.method?.toUpperCase(), config.url) // Debug log
    
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url) // Debug log
    return response
  },
  async (error) => {
    console.error('❌ Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
      data: error.response?.data
    })

    const originalRequest = error.config

    // If 401 and we haven't retried yet, try refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        // Use relative path for refresh too
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        })

        const { access_token } = response.data
        localStorage.setItem('access_token', access_token)
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/auth/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api