import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import Input from '@/components/common/Input'
import Button from '@/components/common/Button'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore(state => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { data } = await api.post('/auth/login', formData)
      setAuth(data.user, data.access_token)
      toast.success('Welcome back!')
      navigate('/datasets')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold">Log in to Helpuvio</h2>
          <p className="mt-2 text-gray-600">Access your purchased datasets</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />

          <Input
            label="Password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
          />

          <Button type="submit" loading={loading} className="w-full">
            Log In
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/auth/signup" className="text-primary-600 hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}