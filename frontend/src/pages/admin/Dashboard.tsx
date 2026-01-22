import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { formatPrice } from '@/lib/utils'

interface Stats {
  total_revenue: number
  total_purchases: number
  total_users: number
  total_datasets: number
  recent_purchases: any[]
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatPrice(stats?.total_revenue || 0)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Purchases</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_purchases || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Users</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_users || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Datasets</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_datasets || 0}</p>
        </div>
      </div>

      {/* Recent Purchases */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Recent Purchases</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Dataset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats?.recent_purchases?.map((purchase: any) => (
                <tr key={purchase.id}>
                  <td className="px-6 py-4 text-sm text-gray-900">{purchase.user_email}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{purchase.dataset_name}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {formatPrice(purchase.amount_cents)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(purchase.paid_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
