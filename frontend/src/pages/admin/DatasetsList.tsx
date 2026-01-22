import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import { formatPrice } from '@/lib/utils'

export default function AdminDatasetsList() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      const response = await api.get('/admin/datasets')
      setDatasets(response.data)
    } catch (error) {
      console.error('Failed to fetch datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTogglePublish = async (id: number, currentStatus: boolean) => {
    try {
      await api.patch(`/admin/datasets/${id}`, {
        is_published: !currentStatus
      })
      fetchDatasets()
    } catch (error) {
      alert('Failed to update dataset')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this dataset?')) {
      return
    }

    try {
      await api.delete(`/admin/datasets/${id}`)
      fetchDatasets()
    } catch (error) {
      alert('Failed to delete dataset')
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Manage Datasets</h1>
        <Link
          to="/admin/datasets/new"
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          + New Dataset
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading datasets...</div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Companies
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Sales
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {datasets.map((dataset) => (
                <tr key={dataset.id}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {dataset.name}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      dataset.is_published
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {dataset.is_published ? 'Published' : 'Draft'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {dataset.company_count.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {formatPrice(dataset.price_cents)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {dataset.total_purchases}
                  </td>
                  <td className="px-6 py-4 text-sm space-x-2">
                    <button
                      onClick={() => handleTogglePublish(dataset.id, dataset.is_published)}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      {dataset.is_published ? 'Unpublish' : 'Publish'}
                    </button>
                    <Link
                      to={`/admin/datasets/${dataset.id}/edit`}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(dataset.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
