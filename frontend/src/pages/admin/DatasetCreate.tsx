import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { useForm } from 'react-hook-form'
import { ArrowLeft, LogOut, Upload, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface DatasetForm {
  name: string
  description: string
  location: string
  category_id: number
  company_count: number
  enrichment_level: 'phone_only' | 'email_and_phone'
  price_cents: number
  csv_file_path: string
  sample_preview_json?: string
}

interface Category {
  id: number
  name: string
  slug: string
  icon?: string
}

interface UploadedFile {
  file_path: string
  filename: string
  company_count: number
  enrichment_level: 'phone_only' | 'email_and_phone'
  headers: string[]
  sample_preview: any[]
}

export default function DatasetCreate() {
  const navigate = useNavigate()
  const { admin, adminLogout } = useAuthStore()
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<DatasetForm>({
    defaultValues: {
      enrichment_level: 'phone_only',
      company_count: 0,
      price_cents: 1999
    }
  })

  const enrichmentLevel = watch('enrichment_level')

  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      const response = await adminApi.get('/datasets/categories')
      setCategories(response.data)
    } catch (error) {
      console.error('Failed to fetch categories:', error)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0])
    }
  }

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file')
      return
    }

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', file)

      const response = await adminApi.post('/admin/datasets/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const data = response.data
      setUploadedFile(data)

      // Auto-fill form fields
      setValue('csv_file_path', data.file_path)
      setValue('company_count', data.company_count)
      setValue('enrichment_level', data.enrichment_level)
      setValue('sample_preview_json', JSON.stringify(data.sample_preview))

      toast.success('CSV uploaded successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload CSV')
    } finally {
      setUploading(false)
    }
  }

  const onSubmit = async (data: DatasetForm) => {
    if (!uploadedFile) {
      toast.error('Please upload a CSV file first')
      return
    }

    try {
      setLoading(true)
      await adminApi.post('/admin/datasets', data)
      toast.success('Dataset created')
      navigate('/admin/datasets')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Failed to create dataset')
    } finally {
      setLoading(false)
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

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back link */}
        <Link to="/admin/datasets" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Datasets
        </Link>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Dataset</h2>

          {/* File Upload Section */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload CSV File *
            </label>

            {!uploadedFile ? (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center ${
                  dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
                }`}
              >
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="csv-upload"
                  disabled={uploading}
                />
                <label htmlFor="csv-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    {uploading ? 'Uploading...' : 'Drag and drop your CSV file here, or click to browse'}
                  </p>
                  <p className="text-sm text-gray-500">CSV files only</p>
                </label>
              </div>
            ) : (
              <div className="border border-green-200 bg-green-50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-green-900">{uploadedFile.filename}</p>
                      <p className="text-sm text-green-700 mt-1">
                        {uploadedFile.company_count} companies • {uploadedFile.enrichment_level === 'email_and_phone' ? 'Email + Phone' : 'Phone Only'}
                      </p>
                      <p className="text-xs text-green-600 mt-1">
                        Columns: {uploadedFile.headers.join(', ')}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setUploadedFile(null)
                      setValue('csv_file_path', '')
                      setValue('company_count', 0)
                    }}
                    className="text-red-600 hover:text-red-700"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {/* Preview */}
                {uploadedFile.sample_preview.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-green-200">
                    <p className="text-sm font-medium text-green-900 mb-2">Preview (first 5 rows):</p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr className="bg-green-100">
                            {uploadedFile.headers.map((header, idx) => (
                              <th key={idx} className="px-2 py-1 text-left text-green-900">{header}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {uploadedFile.sample_preview.map((row, idx) => (
                            <tr key={idx} className="border-t border-green-200">
                              {uploadedFile.headers.map((header, cellIdx) => (
                                <td key={cellIdx} className="px-2 py-1 text-green-800">{row[header]}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset Name *
              </label>
              <input
                type="text"
                {...register('name', { required: 'Name is required' })}
                className={`input ${errors.name ? 'input-error' : ''}`}
                placeholder="e.g., Tech Companies - California"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                {...register('description')}
                rows={3}
                className="input"
                placeholder="Describe what's in this dataset..."
              />
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                {...register('location')}
                className="input"
                placeholder="e.g., San Francisco, CA"
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                {...register('category_id', { required: 'Category is required' })}
                className={`input ${errors.category_id ? 'input-error' : ''}`}
              >
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.icon} {cat.name}
                  </option>
                ))}
              </select>
              {errors.category_id && (
                <p className="mt-1 text-sm text-red-500">{errors.category_id.message}</p>
              )}
            </div>

            {/* Company Count (Auto-filled) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Number of Companies * (Auto-detected)
              </label>
              <input
                type="number"
                {...register('company_count', {
                  required: 'Company count is required',
                  min: { value: 1, message: 'Must be at least 1' }
                })}
                className={`input bg-gray-50 ${errors.company_count ? 'input-error' : ''}`}
                readOnly
              />
              {errors.company_count && (
                <p className="mt-1 text-sm text-red-500">{errors.company_count.message}</p>
              )}
            </div>

            {/* Enrichment Level (Auto-detected) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Type * (Auto-detected)
              </label>
              <div className="grid grid-cols-2 gap-4">
                <label className={`flex items-center p-4 border rounded-lg ${enrichmentLevel === 'phone_only' ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-gray-50'}`}>
                  <input
                    type="radio"
                    value="phone_only"
                    {...register('enrichment_level')}
                    className="mr-3"
                    disabled
                  />
                  <div>
                    <div className="font-medium">Phone Only</div>
                    <div className="text-sm text-gray-500">Companies with verified phone</div>
                  </div>
                </label>
                <label className={`flex items-center p-4 border rounded-lg ${enrichmentLevel === 'email_and_phone' ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-gray-50'}`}>
                  <input
                    type="radio"
                    value="email_and_phone"
                    {...register('enrichment_level')}
                    className="mr-3"
                    disabled
                  />
                  <div>
                    <div className="font-medium">Email + Phone</div>
                    <div className="text-sm text-gray-500">Premium: Both email & phone</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price (in cents) *
              </label>
              <div className="flex items-center">
                <span className="text-gray-500 mr-2">₦</span>
                <input
                  type="number"
                  {...register('price_cents', {
                    required: 'Price is required',
                    min: { value: 100, message: 'Minimum ₦1.00' }
                  })}
                  className={`input ${errors.price_cents ? 'input-error' : ''}`}
                  placeholder="1999"
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">Enter price in kobo (1999 = ₦19.99)</p>
              {errors.price_cents && (
                <p className="mt-1 text-sm text-red-500">{errors.price_cents.message}</p>
              )}
            </div>

            {/* Hidden fields */}
            <input type="hidden" {...register('csv_file_path')} />
            <input type="hidden" {...register('sample_preview_json')} />

            {/* Submit */}
            <div className="flex justify-end space-x-4 pt-4">
              <Link to="/admin/datasets" className="btn btn-outline btn-md">
                Cancel
              </Link>
              <button
                type="submit"
                disabled={loading || !uploadedFile}
                className="btn btn-primary btn-md"
              >
                {loading ? 'Creating...' : 'Create Dataset'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
