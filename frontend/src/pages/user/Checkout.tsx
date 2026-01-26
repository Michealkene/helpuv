import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader } from 'lucide-react'

// This page is a redirect - actual checkout happens through Paystack
export default function Checkout() {
  const { datasetId } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    // Redirect to dataset detail if accessed directly
    // The purchase flow is: Dataset Detail → Create Purchase API → Paystack redirect
    if (datasetId) {
      navigate(`/datasets/${datasetId}`)
    } else {
      navigate('/datasets')
    }
  }, [datasetId, navigate])

  return (
    <div className="flex justify-center items-center py-20">
      <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      <span className="ml-2 text-gray-600">Redirecting to checkout...</span>
    </div>
  )
}
