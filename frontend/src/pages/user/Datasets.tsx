// frontend/src/pages/user/Datasets.tsx
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'

interface Dataset {
  id: number
  name: string
  slug: string
  description: string
  price_cents: number
  company_count: number
  location: string
  enrichment_level: string
}

export default function Datasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    category: '',
    location: '',
    minPrice: '',
    maxPrice: ''
  })

  useEffect(() => {
    fetchDatasets()
  }, [filters])

  const fetchDatasets = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Build query params
      const params = new URLSearchParams()
      if (filters.category) params.append('category', filters.category)
      if (filters.location) params.append('location', filters.location)
      if (filters.minPrice) params.append('min_price', filters.minPrice)
      if (filters.maxPrice) params.append('max_price', filters.maxPrice)

      const response = await api.get(`/datasets?${params.toString()}`)
      
      // Ensure response is an array
      const data = Array.isArray(response.data) ? response.data : []
      setDatasets(data)
    } catch (err: any) {
      console.error('Error fetching datasets:', err)
      
      if (err.response) {
        // Server responded with error
        setError(`Server error: ${err.response.data?.detail || err.response.statusText}`)
      } else if (err.request) {
        // Request made but no response
        setError('Cannot connect to server. Please check if the backend is running.')
      } else {
        // Something else happened
        setError(`Error: ${err.message}`)
      }
      
      setDatasets([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading datasets...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <div className="text-red-600 text-center mb-4">
            <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-semibold mb-2">Connection Error</h2>
            <p className="text-sm text-gray-600">{error}</p>
          </div>
          <button
            onClick={fetchDatasets}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition"
          >
            Try Again
          </button>
          <div className="mt-4 text-xs text-gray-500 text-center">
            <p>API URL: {import.meta.env.VITE_API_URL}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Browse Datasets</h1>
          <p className="text-gray-600 mt-2">Find the perfect lead data for your business</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Categories</option>
                <option value="technology">Technology</option>
                <option value="finance">Finance</option>
                <option value="healthcare">Healthcare</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
              <input
                type="text"
                value={filters.location}
                onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                placeholder="e.g., Austin, TX"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Min Price</label>
              <input
                type="number"
                value={filters.minPrice}
                onChange={(e) => setFilters({ ...filters, minPrice: e.target.value })}
                placeholder="$0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Price</label>
              <input
                type="number"
                value={filters.maxPrice}
                onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
                placeholder="$1000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Found <span className="font-semibold">{datasets.length}</span> datasets
            </p>
            <button
              onClick={() => setFilters({ category: '', location: '', minPrice: '', maxPrice: '' })}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Datasets Grid */}
        {datasets.length === 0 ? (
          <div className="text-center py-16">
            <svg className="w-24 h-24 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets found</h3>
            <p className="text-gray-600">Try adjusting your filters or check back later.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {datasets.map((dataset) => (
              <Link
                key={dataset.id}
                to={`/datasets/${dataset.slug}`}
                className="bg-white rounded-lg shadow-sm hover:shadow-lg transition-shadow duration-200 overflow-hidden group"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900 group-hover:text-blue-600 transition">
                      {dataset.name}
                    </h3>
                    <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                      {dataset.enrichment_level}
                    </span>
                  </div>

                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {dataset.description || 'No description available'}
                  </p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-500">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      {dataset.company_count.toLocaleString()} companies
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {dataset.location || 'Global'}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <span className="text-2xl font-bold text-gray-900">
                      ${(dataset.price_cents / 100).toFixed(2)}
                    </span>
                    <span className="text-blue-600 font-medium group-hover:underline">
                      View Details →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}