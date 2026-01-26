import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Dataset } from '@/types'

export function useDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/datasets')
      .then(res => setDatasets(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return { datasets, loading, error }
}