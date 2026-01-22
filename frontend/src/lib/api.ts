import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

// Get API URL from environment or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data
          localStorage.setItem('access_token', access_token)

          // Retry original request
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred'
    
    console.error('API Error:', {
      status: error.response?.status,
      message: errorMessage,
      url: error.config?.url,
    })

    return Promise.reject({
      status: error.response?.status,
      message: errorMessage,
      data: error.response?.data,
    })
  }
)

// API endpoints
export const authAPI = {
  signup: (data: { email: string; password: string; name: string }) =>
    api.post('/auth/signup', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  
  googleAuth: (credential: string) =>
    api.post('/auth/google', { credential }),
  
  logout: () =>
    api.post('/auth/logout'),
  
  me: () =>
    api.get('/auth/me'),
}

export const datasetsAPI = {
  list: (params?: {
    category?: string
    location?: string
    min_price?: number
    max_price?: number
    search?: string
    page?: number
    limit?: number
  }) => api.get('/datasets', { params }),
  
  get: (slug: string) =>
    api.get(`/datasets/${slug}`),
  
  categories: () =>
    api.get('/datasets/categories'),
}

export const purchasesAPI = {
  create: (datasetId: number) =>
    api.post('/purchases', { dataset_id: datasetId }),
  
  list: () =>
    api.get('/purchases'),
  
  get: (purchaseId: string) =>
    api.get(`/purchases/${purchaseId}`),
}

export const downloadsAPI = {
  get: (purchaseId: string) =>
    api.get(`/downloads/${purchaseId}`),
  
  list: () =>
    api.get('/downloads'),
}

export const adminAPI = {
  // Datasets
  createDataset: (data: FormData) =>
    api.post('/admin/datasets', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  updateDataset: (id: number, data: any) =>
    api.put(`/admin/datasets/${id}`, data),
  
  deleteDataset: (id: number) =>
    api.delete(`/admin/datasets/${id}`),
  
  // Purchases
  listPurchases: (params?: { status?: string; limit?: number }) =>
    api.get('/admin/purchases', { params }),
  
  getPurchase: (id: string) =>
    api.get(`/admin/purchases/${id}`),
  
  refund: (id: string, reason: string) =>
    api.post(`/admin/purchases/${id}/refund`, { reason }),
  
  // Users
  listUsers: () =>
    api.get('/admin/users'),
  
  getUser: (id: string) =>
    api.get(`/admin/users/${id}`),
  
  // Analytics
  analytics: () =>
    api.get('/admin/analytics'),
}

export default api