export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
  email_verified: boolean
  is_active: boolean
  created_at: string
}

export interface Category {
  id: number
  name: string
  slug: string
  icon?: string
}

export interface Dataset {
  id: number
  name: string
  slug: string
  description: string
  category?: Category
  location: string
  company_count: number
  enrichment_level: 'company_only' | 'company_contacts'
  price: number
  sample_preview_json?: any[]
  is_published: boolean
  total_purchases: number
  is_purchased: boolean
  created_at: string
  updated_at: string
}

export interface Purchase {
  id: string
  dataset: {
    id: number
    name: string
    slug: string
    company_count: number
  }
  amount: number
  status: 'pending' | 'paid' | 'failed' | 'refunded'
  payment_url?: string
  created_at: string
  paid_at?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface DashboardStats {
  total_users: number
  total_datasets: number
  total_purchases: number
  total_revenue: number
  revenue_this_month: number
  purchases_this_month: number
  signups_this_month: number
}