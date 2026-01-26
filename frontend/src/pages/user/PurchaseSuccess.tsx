import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '@/lib/api'
import { CheckCircle, Download, Loader } from 'lucide-react'
import toast from 'react-hot-toast'

export default function PurchaseSuccess() {
  const [searchParams] = useSearchParams()
  const purchaseId = searchParams.get('purchase_id')
  
  const [verifying, setVerifying] = useState(true)
  const [_verified, setVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (purchaseId) {
      verifyPurchase()
    } else {
      setVerifying(false)
      setError('No purchase ID found')
    }
  }, [purchaseId])

  const verifyPurchase = async () => {
    try {
      const response = await api.get(`/purchases/${purchaseId}/verify`)
      
      if (response.data.status === 'success') {
        setVerified(true)
        toast.success('Payment confirmed!')
      } else if (response.data.status === 'pending') {
        // Payment still processing, wait and retry
        setTimeout(verifyPurchase, 3000)
        return
      } else {
        setError('Payment verification failed')
      }
    } catch (err) {
      setError('Unable to verify payment')
    } finally {
      setVerifying(false)
    }
  }

  const handleDownload = async () => {
    if (!purchaseId) return

    try {
      const response = await api.get(`/downloads/${purchaseId}`)
      window.location.href = response.data.download_url
      toast.success('Download started')
    } catch (err) {
      toast.error('Download failed')
    }
  }

  if (verifying) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <Loader className="w-16 h-16 text-primary-600 mx-auto mb-6 animate-spin" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Verifying Payment
        </h1>
        <p className="text-gray-600">
          Please wait while we confirm your payment...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl">❌</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Something went wrong
        </h1>
        <p className="text-gray-600 mb-6">{error}</p>
        <div className="space-x-4">
          <Link to="/datasets" className="btn btn-primary btn-md">
            Browse Datasets
          </Link>
          <a href="mailto:support@helpuvio.com" className="btn btn-outline btn-md">
            Contact Support
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-20 text-center">
      <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-6" />
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Purchase Successful!
      </h1>
      <p className="text-gray-600 mb-8">
        Thank you for your purchase. Your dataset is ready to download.
      </p>
      
      <div className="space-y-4">
        <button
          onClick={handleDownload}
          className="w-full btn btn-primary btn-lg flex items-center justify-center"
        >
          <Download className="w-5 h-5 mr-2" />
          Download CSV Now
        </button>
        
        <Link
          to="/downloads"
          className="block w-full btn btn-outline btn-lg"
        >
          Go to My Downloads
        </Link>
      </div>

      <p className="mt-8 text-sm text-gray-500">
        A receipt has been sent to your email. You can re-download this dataset anytime from your Downloads page.
      </p>
    </div>
  )
}
