import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import Input from '@/components/common/Input'
import Button from '@/components/common/Button'
import toast from 'react-hot-toast'

export default function Signup() {
  const navigate = useNavigate()
  const setAuth = useAuthStore(state => state.setAuth)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { data } = await api.post('/auth/signup', formData)
      setAuth(data.user, data.access_token)
      toast.success('Account created successfully!')
      navigate('/datasets')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold">Create your account</h2>
          <p className="mt-2 text-gray-600">Start browsing datasets today</p>
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
            label="Name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <Input
            label="Password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
          />

          <Button type="submit" loading={loading} className="w-full">
            Sign Up
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/auth/login" className="text-primary-600 hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}