import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '@/lib/api'
import { formatPrice, getEnrichmentLabel, formatNumber, formatDate } from '@/lib/utils'
import type { DatasetDetail } from '@/types'
import { useAuthStore } from '@/store/authStore'
import { Check, Download, Shield, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DatasetDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  
  const [dataset, setDataset] = useState<DatasetDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [purchasing, setPurchasing] = useState(false)
  const [alreadyPurchased, setAlreadyPurchased] = useState(false)
  const [purchaseId, setPurchaseId] = useState<string | null>(null)

  useEffect(() => {
    if (slug) {
      fetchDataset()
      if (isAuthenticated) {
        checkPurchaseStatus()
      }
    }
  }, [slug, isAuthenticated])

  const fetchDataset = async () => {
    try {
      setLoading(true)
      const response = await api.get<DatasetDetail>(`/datasets/${slug}`)
      setDataset(response.data)
    } catch (error) {
      console.error('Failed to fetch dataset:', error)
      toast.error('Dataset not found')
      navigate('/datasets')
    } finally {
      setLoading(false)
    }
  }

  const checkPurchaseStatus = async () => {
    try {
      const response = await api.get(`/datasets/${slug}/check-purchase`)
      setAlreadyPurchased(response.data.purchased)
      setPurchaseId(response.data.purchase_id)
    } catch (error) {
      console.error('Failed to check purchase status:', error)
    }
  }

  const handlePurchase = async () => {
    if (!isAuthenticated) {
      toast.error('Please sign in to purchase')
      navigate('/login', { state: { returnTo: `/datasets/${slug}` } })
      return
    }

    if (!dataset) return

    try {
      setPurchasing(true)
      const response = await api.post('/purchases', {
        dataset_id: dataset.id
      })

      if (response.data.already_owned) {
        toast.success('You already own this dataset')
        navigate('/downloads')
        return
      }

      // Redirect to Paystack
      window.location.href = response.data.payment_url
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Purchase failed')
    } finally {
      setPurchasing(false)
    }
  }

  const handleDownload = async () => {
    if (!purchaseId) return

    try {
      const response = await api.get(`/downloads/${purchaseId}`)
      window.location.href = response.data.download_url
      toast.success('Download started')
    } catch (error) {
      toast.error('Download failed')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  if (!dataset) {
    return null
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-2">
              {dataset.category?.icon && (
                <span className="text-3xl">{dataset.category.icon}</span>
              )}
              <span className="badge badge-primary">{dataset.category?.name}</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              {dataset.name}
            </h1>
            <p className="text-lg text-gray-600">
              {dataset.description}
            </p>
          </div>

          {/* What's Included */}
          <div className="bg-gray-50 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              What's Included
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {dataset.fields.map((field) => (
                <div key={field.id} className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-2" />
                  <span className="text-gray-700">
                    {field.field_label || field.field_name}
                  </span>
                  {field.is_enriched && (
                    <span className="ml-2 badge badge-success text-xs">Premium</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Sample Preview */}
          {dataset.sample_preview_json && dataset.sample_preview_json.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Sample Preview
              </h2>
              <div className="overflow-x-auto border rounded-lg">
                <table className="min-w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      {Object.keys(dataset.sample_preview_json[0]).map((key) => (
                        <th key={key} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {dataset.sample_preview_json.map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((value, cellIdx) => (
                          <td key={cellIdx} className="px-4 py-3 text-sm text-gray-600">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                * Email addresses and phone numbers are redacted in preview. Full data available after purchase.
              </p>
            </div>
          )}

          {/* FAQ */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              <details className="bg-gray-50 rounded-lg p-4">
                <summary className="font-medium cursor-pointer">
                  What format is the data in?
                </summary>
                <p className="mt-2 text-gray-600">
                  All datasets are delivered as CSV files, which can be opened in Excel, Google Sheets, or imported into any CRM.
                </p>
              </details>
              <details className="bg-gray-50 rounded-lg p-4">
                <summary className="font-medium cursor-pointer">
                  How fresh is the data?
                </summary>
                <p className="mt-2 text-gray-600">
                  We update our datasets regularly. The last update date is shown on each dataset page.
                  {dataset.last_updated_at && ` This dataset was last updated on ${formatDate(dataset.last_updated_at)}.`}
                </p>
              </details>
              <details className="bg-gray-50 rounded-lg p-4">
                <summary className="font-medium cursor-pointer">
                  Can I re-download my purchase?
                </summary>
                <p className="mt-2 text-gray-600">
                  Yes! You can re-download your purchased datasets anytime from your Downloads page. No additional charges.
                </p>
              </details>
              <details className="bg-gray-50 rounded-lg p-4">
                <summary className="font-medium cursor-pointer">
                  What is your refund policy?
                </summary>
                <p className="mt-2 text-gray-600">
                  We offer a 7-day money-back guarantee if the data quality doesn't meet your expectations. Contact support for refunds.
                </p>
              </details>
            </div>
          </div>
        </div>

        {/* Sidebar - Pricing Card */}
        <div className="lg:col-span-1">
          <div className="sticky top-24">
            <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
              {/* Price */}
              <div className="text-center mb-6">
                <div className="text-4xl font-bold text-primary-600 mb-2">
                  {formatPrice(dataset.price_cents)}
                </div>
                <div className="text-gray-600">
                  {formatNumber(dataset.company_count)} companies
                </div>
                <div className="mt-2">
                  <span className={`badge ${dataset.enrichment_level === 'email_and_phone' ? 'badge-success' : 'badge-primary'}`}>
                    {getEnrichmentLabel(dataset.enrichment_level)}
                  </span>
                </div>
              </div>

              {/* Action Button */}
              {alreadyPurchased ? (
                <button
                  onClick={handleDownload}
                  className="w-full btn btn-primary btn-lg flex items-center justify-center"
                >
                  <Download className="w-5 h-5 mr-2" />
                  Download CSV
                </button>
              ) : (
                <button
                  onClick={handlePurchase}
                  disabled={purchasing}
                  className="w-full btn btn-primary btn-lg"
                >
                  {purchasing ? 'Processing...' : 'Purchase Now'}
                </button>
              )}

              {/* Trust Signals */}
              <div className="mt-6 space-y-3">
                <div className="flex items-center text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500 mr-2" />
                  <span>Instant CSV download</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <RefreshCw className="w-4 h-4 text-green-500 mr-2" />
                  <span>Unlimited re-downloads</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Shield className="w-4 h-4 text-green-500 mr-2" />
                  <span>7-day money-back guarantee</span>
                </div>
              </div>

              {/* Payment Info */}
              <div className="mt-6 pt-6 border-t text-center text-sm text-gray-500">
                Secure payment via Paystack
              </div>
            </div>

            {/* Stats */}
            <div className="mt-4 bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total purchases</span>
                <span className="font-medium">{dataset.total_purchases}</span>
              </div>
              {dataset.last_updated_at && (
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-gray-600">Last updated</span>
                  <span className="font-medium">{formatDate(dataset.last_updated_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
