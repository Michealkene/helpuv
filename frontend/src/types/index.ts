// ============================================================
// User Types
// ============================================================

export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
  email_verified: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// ============================================================
// Category Types
// ============================================================

export interface Category {
  id: number
  name: string
  slug: string
  icon?: string
  description?: string
}

// ============================================================
// Dataset Types
// ============================================================

export interface DatasetField {
  id: number
  field_name: string
  field_label?: string
  is_enriched: boolean
  display_order: number
}

export interface Dataset {
  id: number
  name: string
  slug: string
  description?: string
  location?: string
  company_count: number
  enrichment_level: 'phone_only' | 'email_and_phone'
  price_cents: number
  category?: Category
  total_purchases: number
}

export interface DatasetDetail extends Dataset {
  fields: DatasetField[]
  sample_preview_json?: Record<string, unknown>[]
  last_updated_at?: string
  created_at: string
}

export interface PaginatedDatasets {
  items: Dataset[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ============================================================
// Purchase Types
// ============================================================

export interface DatasetBrief {
  id: number
  name: string
  slug: string
  company_count: number
  enrichment_level: string
}

export interface Purchase {
  id: string
  dataset?: DatasetBrief
  amount_cents: number
  status: 'pending' | 'paid' | 'failed' | 'refunded'
  paid_at?: string
  created_at: string
}

export interface PurchaseCreateResponse {
  purchase_id: string
  payment_url: string
  amount_cents: number
  dataset_name: string
  message: string
}

// ============================================================
// Download Types
// ============================================================

export interface DownloadResponse {
  download_url: string
  expires_in: number
  filename: string
}

// ============================================================
// Admin Types
// ============================================================

export interface AdminUser {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
  created_at: string
  last_login_at?: string
}

export interface AdminAuthResponse {
  access_token: string
  token_type: string
  admin: AdminUser
}

export interface DashboardStats {
  total_revenue_cents: number
  total_purchases: number
  total_users: number
  total_datasets: number
  revenue_this_month: number
  purchases_this_month: number
  signups_this_month: number
  revenue_change?: number
}

export interface RevenueDataPoint {
  date: string
  revenue_cents: number
  purchases: number
}

export interface DashboardData {
  stats: DashboardStats
  revenue_chart: RevenueDataPoint[]
  top_datasets: {
    name: string
    slug: string
    purchases: number
    revenue_cents: number
  }[]
  recent_purchases: {
    id: string
    user_email: string
    dataset_name: string
    amount_cents: number
    paid_at: string
  }[]
}

// ============================================================
// API Error Type
// ============================================================

export interface APIError {
  detail: string
}
