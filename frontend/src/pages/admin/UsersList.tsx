import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { formatDate, formatPrice } from '@/lib/utils'
import { LogOut, UserX, UserCheck } from 'lucide-react'
import toast from 'react-hot-toast'

interface User {
  id: string
  email: string
  name: string
  is_active: boolean
  email_verified: boolean
  created_at: string
  last_login_at?: string
  total_purchases: number
  total_spent_cents: number
}

export default function AdminUsersList() {
  const navigate = useNavigate()
  const { admin, adminLogout } = useAuthStore()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await adminApi.get('/admin/users')
      setUsers(response.data.items)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const toggleUserStatus = async (user: User) => {
    try {
      await adminApi.patch(`/admin/users/${user.id}/status`, {
        is_active: !user.is_active
      })
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}`)
      fetchUsers()
    } catch (error) {
      toast.error('Failed to update user')
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
              className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 px-1 py-4 text-sm font-medium"
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
              className="border-b-2 border-primary-500 text-primary-600 px-1 py-4 text-sm font-medium"
            >
              Users
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Users</h2>
            <p className="text-gray-600">Manage user accounts</p>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg shadow">
            <p className="text-gray-600">No users yet</p>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="table">
              <thead className="bg-gray-50">
                <tr>
                  <th>User</th>
                  <th>Joined</th>
                  <th>Last Login</th>
                  <th>Purchases</th>
                  <th>Total Spent</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <div className="font-medium text-gray-900">{user.name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </td>
                    <td className="text-gray-600">{formatDate(user.created_at)}</td>
                    <td className="text-gray-600">
                      {user.last_login_at ? formatDate(user.last_login_at) : 'Never'}
                    </td>
                    <td className="text-gray-600">{user.total_purchases}</td>
                    <td className="font-medium">{formatPrice(user.total_spent_cents)}</td>
                    <td>
                      <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => toggleUserStatus(user)}
                        className={`p-1 rounded hover:bg-gray-100 ${user.is_active ? 'text-red-500' : 'text-green-500'}`}
                        title={user.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {user.is_active ? (
                          <UserX className="w-4 h-4" />
                        ) : (
                          <UserCheck className="w-4 h-4" />
                        )}
                      </button>
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
