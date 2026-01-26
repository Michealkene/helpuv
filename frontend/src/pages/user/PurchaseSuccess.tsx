import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '@/lib/api'

export default function PurchaseSuccess() {
  const [searchParams] = useSearchParams()
  const purchaseId = searchParams.get('purchase_id')
  const [purchase, setPurchase] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (purchaseId) {
      verifyPurchase()
    }
  }, [purchaseId])

  const verifyPurchase = async () => {
    try {
      const response = await api.get(`/purchases/${purchaseId}`)
      setPurchase(response.data)
    } catch (error) {
      console.error('Failed to verify purchase:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Verifying your purchase...</p>
      </div>
    )
  }

  if (!purchase) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="text-red-500 text-5xl mb-4">✗</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Purchase Not Found</h1>
        <p className="text-gray-600 mb-8">
          We couldn't find your purchase. Please contact support if you believe this is an error.
        </p>
        <Link
          to="/datasets"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
        >
          Browse Datasets
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
      <div className="text-green-500 text-5xl mb-4">✓</div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Purchase Successful!</h1>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8 text-left">
        <h2 className="text-xl font-semibold mb-4">Order Details</h2>
        <dl className="space-y-2">
          <div className="flex justify-between">
            <dt className="text-gray-600">Dataset:</dt>
            <dd className="font-medium">{purchase.dataset?.name}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Amount Paid:</dt>
            <dd className="font-medium">${(purchase.amount_cents / 100).toFixed(2)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-600">Purchase Date:</dt>
            <dd className="font-medium">
              {new Date(purchase.paid_at).toLocaleDateString()}
            </dd>
          </div>
        </dl>
      </div>

      <p className="text-gray-600 mb-8">
        Your dataset is ready to download! You can access it anytime from your Downloads page.
      </p>

      <div className="flex justify-center space-x-4">
        <Link
          to="/downloads"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
        >
          Go to Downloads
        </Link>
        <Link
          to="/datasets"
          className="bg-white text-blue-600 px-6 py-3 rounded-lg hover:bg-gray-50 font-semibold border border-blue-600"
        >
          Browse More Datasets
        </Link>
      </div>
    </div>
  )
}
