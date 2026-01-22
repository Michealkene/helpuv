import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import { formatPrice, formatDate } from '@/lib/utils'

interface Purchase {
  id: string
  dataset: {
    id: number
    name: string
    company_count: number
  }
  amount_cents: number
  paid_at: string
}

export default function Downloads() {
  const { user } = useAuthStore()
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [loading, setLoading] = useState(true)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      fetchPurchases()
    }
  }, [user])

  const fetchPurchases = async () => {
    try {
      const response = await api.get('/purchases')
      setPurchases(response.data)
    } catch (error) {
      console.error('Failed to fetch purchases:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (purchaseId: string, datasetName: string) => {
    setDownloadingId(purchaseId)
    try {
      const response = await api.get(`/downloads/${purchaseId}`)
      const { download_url } = response.data
      
      // Create temporary link and trigger download
      const link = document.createElement('a')
      link.href = download_url
      link.download = `${datasetName.toLowerCase().replace(/\s+/g, '-')}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download failed. Please try again.')
    } finally {
      setDownloadingId(null)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading your purchases...</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Downloads</h1>

      {purchases.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="text-4xl mb-4">📥</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No purchases yet</h2>
          <p className="text-gray-600 mb-6">
            Browse our dataset catalog to find data for your business
          </p>
          <a
            href="/datasets"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Browse Datasets
          </a>
        </div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dataset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Purchased
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Companies
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchases.map((purchase) => (
                <tr key={purchase.id}>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {purchase.dataset.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDate(purchase.paid_at)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {purchase.dataset.company_count.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {formatPrice(purchase.amount_cents)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      onClick={() => handleDownload(purchase.id, purchase.dataset.name)}
                      disabled={downloadingId === purchase.id}
                      className="text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                    >
                      {downloadingId === purchase.id ? 'Downloading...' : '⬇ Download CSV'}
                    </button>
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