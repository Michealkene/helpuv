import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import Button from '../common/Button'

export default function Header() {
  const { user, logout } = useAuthStore()
  
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-2xl font-bold text-primary-600">
              Helpuvio
            </Link>
            
            <nav className="hidden md:flex gap-6">
              <Link to="/datasets" className="text-gray-600 hover:text-gray-900">
                Datasets
              </Link>
              {user && (
                <Link to="/downloads" className="text-gray-600 hover:text-gray-900">
                  My Downloads
                </Link>
              )}
            </nav>
          </div>
          
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-sm text-gray-600">
                  {user.name || user.email}
                </span>
                <Button variant="outline" size="sm" onClick={logout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link to="/auth/login">
                  <Button variant="outline" size="sm">
                    Login
                  </Button>
                </Link>
                <Link to="/auth/signup">
                  <Button size="sm">
                    Sign Up
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}