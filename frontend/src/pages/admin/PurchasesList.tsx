import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { formatPrice, formatDate } from '@/lib/utils'

export default function AdminPurchasesList() {
  const [purchases, setPurchases] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPurchases()
  }, [])

  const fetchPurchases = async () => {
    try {
      const response = await api.get('/admin/purchases')
      setPurchases(response.data)
    } catch (error) {
      console.error('Failed to fetch purchases:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefund = async (purchaseId: string) => {
    const reason = prompt('Refund reason:')
    if (!reason) return

    try {
      await api.post(`/admin/purchases/${purchaseId}/refund`, { reason })
      alert('Refund issued successfully')
      fetchPurchases()
    } catch (error) {
      alert('Failed to issue refund')
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">All Purchases</h1>

      {loading ? (
        <div className="text-center py-12">Loading purchases...</div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Order ID
                </th>
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchases.map((purchase) => (
                <tr key={purchase.id}>
                  <td className="px-6 py-4 text-sm font-mono text-gray-900">
                    {purchase.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {purchase.user?.email}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {purchase.dataset?.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {formatPrice(purchase.amount_cents)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDate(purchase.paid_at)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      purchase.status === 'paid'
                        ? 'bg-green-100 text-green-800'
                        : purchase.status === 'refunded'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {purchase.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {purchase.status === 'paid' && (
                      <button
                        onClick={() => handleRefund(purchase.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Issue Refund
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
