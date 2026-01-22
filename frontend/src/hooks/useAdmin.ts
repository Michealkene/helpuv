import { useState, useEffect } from 'react'
import api from '@/lib/api'

export function useAdmin() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/dashboard/stats')
      .then(res => setStats(res.data))
      .finally(() => setLoading(false))
  }, [])

  return { stats, loading }
}