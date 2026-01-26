import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import { formatPrice, formatDate, getEnrichmentLabel } from '@/lib/utils'
import type { Purchase } from '@/types'
import { Download, ShoppingBag } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Downloads() {
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<string | null>(null)

  useEffect(() => {
    fetchPurchases()
  }, [])

  const fetchPurchases = async () => {
    try {
      setLoading(true)
      const response = await api.get<Purchase[]>('/purchases/my-purchases')
      setPurchases(response.data)
    } catch (error) {
      console.error('Failed to fetch purchases:', error)
      toast.error('Failed to load purchases')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (purchaseId: string) => {
    try {
      setDownloading(purchaseId)
      const response = await api.get(`/downloads/${purchaseId}`)
      
      // Trigger download
      window.location.href = response.data.download_url
      toast.success('Download started')
    } catch (error) {
      toast.error('Download failed')
    } finally {
      setDownloading(null)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Downloads</h1>
        <p className="text-gray-600 mt-1">
          Access your purchased datasets anytime
        </p>
      </div>

      {purchases.length === 0 ? (
        <div className="text-center py-20 bg-gray-50 rounded-lg">
          <ShoppingBag className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No purchases yet
          </h3>
          <p className="text-gray-600 mb-6">
            Browse our datasets to find leads for your business
          </p>
          <Link to="/datasets" className="btn btn-primary btn-md">
            Browse Datasets
          </Link>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="table">
            <thead className="bg-gray-50">
              <tr>
                <th>Dataset</th>
                <th>Type</th>
                <th>Companies</th>
                <th>Purchased</th>
                <th>Amount</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {purchases.map((purchase) => (
                <tr key={purchase.id}>
                  <td>
                    <div className="font-medium text-gray-900">
                      {purchase.dataset?.name || 'Unknown Dataset'}
                    </div>
                    {purchase.dataset?.slug && (
                      <Link 
                        to={`/datasets/${purchase.dataset.slug}`}
                        className="text-sm text-primary-600 hover:text-primary-700"
                      >
                        View details →
                      </Link>
                    )}
                  </td>
                  <td className="text-gray-600">
                    {purchase.dataset?.enrichment_level 
                      ? getEnrichmentLabel(purchase.dataset.enrichment_level)
                      : '-'
                    }
                  </td>
                  <td className="text-gray-600">
                    {purchase.dataset?.company_count?.toLocaleString() || '-'}
                  </td>
                  <td className="text-gray-600">
                    {formatDate(purchase.paid_at)}
                  </td>
                  <td className="font-medium text-gray-900">
                    {formatPrice(purchase.amount_cents)}
                  </td>
                  <td>
                    <button
                      onClick={() => handleDownload(purchase.id)}
                      disabled={downloading === purchase.id}
                      className="btn btn-primary btn-sm flex items-center"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      {downloading === purchase.id ? 'Downloading...' : 'Download'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Help Section */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium text-gray-900 mb-2">Need help?</h3>
        <p className="text-gray-600 text-sm">
          You can re-download your purchased datasets anytime. Downloads don't expire.
          If you're having issues, contact us at{' '}
          <a href="mailto:support@helpuvio.com" className="text-primary-600 hover:underline">
            support@helpuvio.com
          </a>
        </p>
      </div>
    </div>
  )
}
