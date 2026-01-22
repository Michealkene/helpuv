export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
export const PAYSTACK_PUBLIC_KEY = import.meta.env.VITE_PAYSTACK_PUBLIC_KEY || ''

export const ROUTES = {
  HOME: '/',
  DATASETS: '/datasets',
  LOGIN: '/auth/login',
  SIGNUP: '/auth/signup',
  DOWNLOADS: '/downloads',
  ADMIN: '/admin',
} as const