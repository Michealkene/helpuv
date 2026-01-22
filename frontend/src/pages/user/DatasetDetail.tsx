import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import { formatPrice } from '@/lib/utils'

interface Dataset {
  id: number
  name: string
  slug: string
  description: string
  category: { name: string }
  location: string
  company_count: number
  price_cents: number
  enrichment_level: string
  sample_preview_json: any[]
  fields: { field_name: string; field_label: string; is_enriched: boolean }[]
}

export default function DatasetDetail() {
  const { slug } = useParams()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDataset()
  }, [slug])

  const fetchDataset = async () => {
    try {
      const response = await api.get(`/datasets/${slug}`)
      setDataset(response.data)
    } catch (error) {
      console.error('Failed to fetch dataset:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePurchase = () => {
    if (!user) {
      navigate('/auth/login')
      return
    }
    navigate(`/checkout/${dataset?.id}`)
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (!dataset) {
    return <div className="text-center py-12">Dataset not found</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{dataset.name}</h1>
          <p className="text-gray-600 mb-8">{dataset.description}</p>

          {/* What's Included */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">What's Included</h2>
            <div className="grid grid-cols-2 gap-4">
              {dataset.fields?.map((field) => (
                <div key={field.field_name} className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700">{field.field_label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sample Preview */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Sample Preview</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    {dataset.sample_preview_json?.[0] && Object.keys(dataset.sample_preview_json[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left font-medium text-gray-700">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.sample_preview_json?.map((row, idx) => (
                    <tr key={idx} className="border-b">
                      {Object.values(row).map((value: any, i) => (
                        <td key={i} className="px-4 py-2 text-gray-600">
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              * Emails and phone numbers are partially redacted in preview. Full data available after purchase.
            </p>
          </div>
        </div>

        {/* Sidebar - Pricing Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-4">
            <div className="text-center mb-6">
              <div className="text-4xl font-bold text-gray-900 mb-2">
                {formatPrice(dataset.price_cents)}
              </div>
              <p className="text-gray-600 text-sm">
                {dataset.company_count.toLocaleString()} companies
              </p>
            </div>

            <button
              onClick={handlePurchase}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold mb-4"
            >
              Purchase Now
            </button>

            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center">
                <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Instant download
              </li>
              <li className="flex items-center">
                <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Unlimited re-downloads
              </li>
              <li className="flex items-center">
                <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                7-day money-back guarantee
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
