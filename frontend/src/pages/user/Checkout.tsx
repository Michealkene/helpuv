import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import { formatPrice } from '@/lib/utils'

export default function Checkout() {
  const { datasetId } = useParams()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  
  const [dataset, setDataset] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user) {
      navigate('/auth/login')
      return
    }
    fetchDataset()
  }, [datasetId, user])

  const fetchDataset = async () => {
    try {
      const response = await api.get(`/datasets/${datasetId}`)
      setDataset(response.data)
    } catch (error) {
      console.error('Failed to fetch dataset:', error)
    }
  }

  const handlePurchase = async () => {
    setLoading(true)
    try {
      const response = await api.post('/purchases', {
        dataset_id: parseInt(datasetId!)
      })
      
      const { authorization_url } = response.data
      
      // Redirect to Paystack
      window.location.href = authorization_url
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Purchase failed')
      setLoading(false)
    }
  }

  if (!dataset) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Order Summary</h2>
        <div className="border-b pb-4 mb-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <p className="font-medium">{dataset.name}</p>
              <p className="text-sm text-gray-600">{dataset.company_count} companies</p>
            </div>
            <p className="font-semibold">{formatPrice(dataset.price_cents)}</p>
          </div>
        </div>
        <div className="flex justify-between text-lg font-bold">
          <span>Total</span>
          <span>{formatPrice(dataset.price_cents)}</span>
        </div>
      </div>

      <button
        onClick={handlePurchase}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Proceed to Payment'}
      </button>

      <p className="text-xs text-gray-500 text-center mt-4">
        By purchasing, you agree to our Terms of Service and Privacy Policy
      </p>
    </div>
  )
}
