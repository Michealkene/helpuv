import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { formatPrice, formatDate, getStatusBadgeClass } from '@/lib/utils'
import { LogOut, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

interface Purchase {
  id: string
  user_email?: string
  amount_cents: number
  paystack_reference: string
  status: string
  paid_at?: string
  created_at: string
}

export default function AdminPurchasesList() {
  const navigate = useNavigate()
  const { admin, adminLogout } = useAuthStore()
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [loading, setLoading] = useState(true)
  const [refunding, setRefunding] = useState<string | null>(null)

  useEffect(() => {
    fetchPurchases()
  }, [])

  const fetchPurchases = async () => {
    try {
      const response = await adminApi.get('/admin/purchases')
      setPurchases(response.data.items)
    } catch (error) {
      console.error('Failed to fetch purchases:', error)
      toast.error('Failed to load purchases')
    } finally {
      setLoading(false)
    }
  }

  const handleRefund = async (purchaseId: string) => {
    const reason = prompt('Enter refund reason:')
    if (!reason) return

    try {
      setRefunding(purchaseId)
      await adminApi.post(`/admin/purchases/${purchaseId}/refund`, { reason })
      toast.success('Refund processed')
      fetchPurchases()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Refund failed')
    } finally {
      setRefunding(null)
    }
  }

  const handleLogout = () => {
    adminLogout()
    navigate('/admin/login')
  }

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
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
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
              className="border-b-2 border-primary-500 text-primary-600 px-1 py-4 text-sm font-medium"
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
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Purchases</h2>
            <p className="text-gray-600">View and manage all purchases</p>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
          </div>
        ) : purchases.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg shadow">
            <p className="text-gray-600">No purchases yet</p>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="table">
              <thead className="bg-gray-50">
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {purchases.map((purchase) => (
                  <tr key={purchase.id}>
                    <td>
                      <div className="font-mono text-sm text-gray-600">
                        {purchase.paystack_reference}
                      </div>
                    </td>
                    <td className="text-gray-900">{purchase.user_email || 'Unknown'}</td>
                    <td className="font-medium">{formatPrice(purchase.amount_cents)}</td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(purchase.status)}`}>
                        {purchase.status}
                      </span>
                    </td>
                    <td className="text-gray-600">
                      {formatDate(purchase.paid_at || purchase.created_at)}
                    </td>
                    <td>
                      {purchase.status === 'paid' && (
                        <button
                          onClick={() => handleRefund(purchase.id)}
                          disabled={refunding === purchase.id}
                          className="text-red-600 hover:text-red-700 text-sm font-medium flex items-center"
                        >
                          <RefreshCw className={`w-3 h-3 mr-1 ${refunding === purchase.id ? 'animate-spin' : ''}`} />
                          Refund
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
