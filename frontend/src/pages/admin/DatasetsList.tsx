import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { formatPrice, getEnrichmentLabel, formatNumber } from '@/lib/utils'
import { Plus, Eye, EyeOff, Trash2, LogOut } from 'lucide-react'
import toast from 'react-hot-toast'

interface AdminDataset {
  id: number
  name: string
  slug: string
  location?: string
  company_count: number
  enrichment_level: string
  price_cents: number
  is_published: boolean
  total_purchases: number
  total_revenue_cents: number
}

export default function AdminDatasetsList() {
  const navigate = useNavigate()
  const { admin, adminLogout } = useAuthStore()
  const [datasets, setDatasets] = useState<AdminDataset[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      const response = await adminApi.get('/admin/datasets')
      setDatasets(response.data)
    } catch (error) {
      console.error('Failed to fetch datasets:', error)
      toast.error('Failed to load datasets')
    } finally {
      setLoading(false)
    }
  }

  const togglePublish = async (dataset: AdminDataset) => {
    try {
      if (dataset.is_published) {
        await adminApi.post(`/admin/datasets/${dataset.id}/unpublish`)
        toast.success('Dataset unpublished')
      } else {
        await adminApi.post(`/admin/datasets/${dataset.id}/publish`)
        toast.success('Dataset published')
      }
      fetchDatasets()
    } catch (error) {
      toast.error('Failed to update dataset')
    }
  }

  const deleteDataset = async (dataset: AdminDataset) => {
    if (!confirm(`Delete "${dataset.name}"? This cannot be undone.`)) {
      return
    }

    try {
      await adminApi.delete(`/admin/datasets/${dataset.id}`)
      toast.success('Dataset deleted')
      fetchDatasets()
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Failed to delete')
    }
  }

  const handleLogout = () => {
    adminLogout()
    navigate('/admin/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">H</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">Admin Dashboard</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">{admin?.email}</span>
            <button onClick={handleLogout} className="btn btn-outline btn-sm">
              <LogOut className="w-4 h-4 mr-1" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <Link
              to="/admin"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Overview
            </Link>
            <Link
              to="/admin/datasets"
              className="border-b-2 border-primary-500 text-primary-600 px-1 py-4 text-sm font-medium"
            >
              Datasets
            </Link>
            <Link
              to="/admin/purchases"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Purchases
            </Link>
            <Link
              to="/admin/users"
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
            >
              Users
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Datasets</h2>
            <p className="text-gray-600">Manage your lead datasets</p>
          </div>
          <Link to="/admin/datasets/new" className="btn btn-primary btn-md">
            <Plus className="w-4 h-4 mr-2" />
            Add Dataset
          </Link>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
          </div>
        ) : datasets.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg shadow">
            <p className="text-gray-600 mb-4">No datasets yet</p>
            <Link to="/admin/datasets/new" className="btn btn-primary btn-md">
              Create your first dataset
            </Link>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="table">
              <thead className="bg-gray-50">
                <tr>
                  <th>Dataset</th>
                  <th>Location</th>
                  <th>Companies</th>
                  <th>Type</th>
                  <th>Price</th>
                  <th>Sales</th>
                  <th>Revenue</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>
                      <div className="font-medium text-gray-900">{dataset.name}</div>
                      <div className="text-sm text-gray-500">{dataset.slug}</div>
                    </td>
                    <td className="text-gray-600">{dataset.location || '-'}</td>
                    <td className="text-gray-600">{formatNumber(dataset.company_count)}</td>
                    <td className="text-gray-600">{getEnrichmentLabel(dataset.enrichment_level)}</td>
                    <td className="font-medium">{formatPrice(dataset.price_cents)}</td>
                    <td className="text-gray-600">{dataset.total_purchases}</td>
                    <td className="font-medium text-green-600">
                      {formatPrice(dataset.total_revenue_cents)}
                    </td>
                    <td>
                      <span className={`badge ${dataset.is_published ? 'badge-success' : 'badge-warning'}`}>
                        {dataset.is_published ? 'Published' : 'Draft'}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => togglePublish(dataset)}
                          className="p-1 hover:bg-gray-100 rounded"
                          title={dataset.is_published ? 'Unpublish' : 'Publish'}
                        >
                          {dataset.is_published ? (
                            <EyeOff className="w-4 h-4 text-gray-500" />
                          ) : (
                            <Eye className="w-4 h-4 text-gray-500" />
                          )}
                        </button>
                        <button
                          onClick={() => deleteDataset(dataset)}
                          className="p-1 hover:bg-gray-100 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
