import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'

export default function Settings() {
  const { user, setUser, logout } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const response = await api.patch('/users/me', {
        name: formData.name,
        email: formData.email
      })
      
      setUser(response.data)
      setMessage('Profile updated successfully')
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.newPassword !== formData.confirmPassword) {
      setMessage('New passwords do not match')
      return
    }

    if (formData.newPassword.length < 8) {
      setMessage('New password must be at least 8 characters')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      await api.post('/users/me/password', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword
      })
      
      setMessage('Password changed successfully')
      setFormData({
        ...formData,
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Password change failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      return
    }

    try {
      await api.delete('/users/me')
      logout()
      window.location.href = '/'
    } catch (error) {
      alert('Failed to delete account. Please contact support.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>

      {message && (
        <div className={`p-4 rounded-lg mb-6 ${
          message.includes('success') 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      {/* Profile Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Profile Information</h2>
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Change Password */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Change Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={formData.currentPassword}
              onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Password
            </label>
            <input
              type="password"
              value={formData.newPassword}
              onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              minLength={8}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-lg border border-red-200 p-6">
        <h2 className="text-xl font-semibold text-red-700 mb-4">Danger Zone</h2>
        <p className="text-gray-600 mb-4">
          Once you delete your account, there is no going back. Please be certain.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700"
        >
          Delete Account
        </button>
      </div>
    </div>
  )
}