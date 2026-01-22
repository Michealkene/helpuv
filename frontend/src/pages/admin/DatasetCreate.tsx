import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '@/lib/api'

export default function AdminDatasetCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    location: '',
    category_id: 1,
    price_cents: 2000,
    enrichment_level: 'company_only'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file) {
      alert('Please upload a CSV file')
      return
    }

    setLoading(true)

    try {
      // Upload file first
      const fileFormData = new FormData()
      fileFormData.append('file', file)
      
      const uploadResponse = await api.post('/admin/datasets/upload', fileFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      const { file_path, company_count } = uploadResponse.data

      // Create dataset
      await api.post('/admin/datasets', {
        ...formData,
        csv_file_path: file_path,
        company_count
      })

      alert('Dataset created successfully!')
      navigate('/admin/datasets')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create dataset')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Dataset</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Slug (URL-friendly) *
              </label>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="e.g., saas-companies-austin-tx"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location *
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="e.g., Austin, TX"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price (cents) *
              </label>
              <input
                type="number"
                value={formData.price_cents}
                onChange={(e) => setFormData({ ...formData, price_cents: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                min={100}
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                ${(formData.price_cents / 100).toFixed(2)}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Enrichment Level *
              </label>
              <select
                value={formData.enrichment_level}
                onChange={(e) => setFormData({ ...formData, enrichment_level: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="company_only">Company Only</option>
                <option value="company_contacts">Company + Contacts</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Upload CSV File</h2>
          
          <div>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
              required
            />
            {file && (
              <p className="text-sm text-gray-600 mt-2">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/admin/datasets')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Dataset'}
          </button>
        </div>
      </form>
    </div>
  )
}