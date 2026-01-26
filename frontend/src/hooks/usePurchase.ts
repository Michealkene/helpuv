import { useState } from 'react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

export function usePurchase() {
  const [loading, setLoading] = useState(false)

  const createPurchase = async (datasetId: number) => {
    setLoading(true)
    try {
      const { data } = await api.post('/purchases', { dataset_id: datasetId })
      return data
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Purchase failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  return { createPurchase, loading }
}