import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { formatPrice, formatDate } from '@/lib/utils'
import type { DashboardData } from '@/types'
import {
  DollarSign,
  ShoppingCart,
  Users,
  TrendingUp,
  TrendingDown,
  LogOut,
  Package,
  Receipt,
  UserCheck
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const { admin, adminLogout } = useAuthStore()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const response = await adminApi.get<DashboardData>('/admin/dashboard')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    adminLogout()
    navigate('/admin/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-gray-600">Failed to load dashboard</p>
      </div>
    )
  }

  const { stats } = data

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">H</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">Admin Dashboard</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">{admin?.email}</span>
            <button onClick={handleLogout} className="btn btn-outline btn-sm">
              <LogOut className="w-4 h-4 mr-1" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <Link
              to="/admin"
              className="border-b-2 border-primary-500 text-primary-600 px-1 py-4 text-sm font-medium"
            >
              Overview
            </Link>
            <Link
              to="/admin/datasets"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Datasets
            </Link>
            <Link
              to="/admin/purchases"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Purchases
            </Link>
            <Link
              to="/admin/users"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Users
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Revenue */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatPrice(stats.total_revenue_cents)}
                </p>
              </div>
            </div>
          </div>

          {/* This Month */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <ShoppingCart className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">This Month</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatPrice(stats.revenue_this_month)}
                </p>
                {stats.revenue_change != null && (
                  <p className={`text-sm flex items-center ${stats.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {stats.revenue_change >= 0 ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {Math.abs(stats.revenue_change ?? 0).toFixed(1)}% vs last month
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Total Purchases */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Receipt className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Total Purchases</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total_purchases}
                </p>
              </div>
            </div>
          </div>

          {/* Total Users */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Users className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Total Users</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total_users}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/admin/datasets/new"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow flex items-center"
          >
            <div className="p-3 bg-primary-100 rounded-lg">
              <Package className="w-6 h-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">Upload Dataset</p>
              <p className="text-sm text-gray-500">Add a new dataset</p>
            </div>
          </Link>

          <Link
            to="/admin/purchases"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow flex items-center"
          >
            <div className="p-3 bg-green-100 rounded-lg">
              <Receipt className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">View Purchases</p>
              <p className="text-sm text-gray-500">Manage orders & refunds</p>
            </div>
          </Link>

          <Link
            to="/admin/users"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow flex items-center"
          >
            <div className="p-3 bg-yellow-100 rounded-lg">
              <UserCheck className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">Manage Users</p>
              <p className="text-sm text-gray-500">View user accounts</p>
            </div>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Top Datasets */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className="font-semibold text-gray-900">Top Datasets</h2>
              <Link to="/admin/datasets" className="text-sm text-primary-600 hover:text-primary-700">
                View all →
              </Link>
            </div>
            <div className="p-6">
              {data.top_datasets.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No datasets yet</p>
              ) : (
                <div className="space-y-4">
                  {data.top_datasets.map((dataset, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{dataset.name}</p>
                        <p className="text-sm text-gray-500">{dataset.purchases} sales</p>
                      </div>
                      <p className="font-medium text-gray-900">
                        {formatPrice(dataset.revenue_cents)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Purchases */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className="font-semibold text-gray-900">Recent Purchases</h2>
              <Link to="/admin/purchases" className="text-sm text-primary-600 hover:text-primary-700">
                View all →
              </Link>
            </div>
            <div className="p-6">
              {data.recent_purchases.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No purchases yet</p>
              ) : (
                <div className="space-y-4">
                  {data.recent_purchases.map((purchase) => (
                    <div key={purchase.id} className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{purchase.user_email}</p>
                        <p className="text-sm text-gray-500">{purchase.dataset_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">
                          {formatPrice(purchase.amount_cents)}
                        </p>
                        <p className="text-sm text-gray-500">
                          {formatDate(purchase.paid_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
