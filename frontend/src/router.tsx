import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import AuthLayout from './components/layout/AuthLayout'

// Public pages
import Landing from './pages/public/Landing'
import Privacy from './pages/public/Privacy'
import Terms from './pages/public/Terms'
import NotFound from './pages/public/NotFound'

// Auth pages
import Login from './pages/auth/Login'
import Signup from './pages/auth/Signup'

// User pages
import Datasets from './pages/user/Datasets'
import DatasetDetail from './pages/user/DatasetDetail'
import Checkout from './pages/user/Checkout'
import PurchaseSuccess from './pages/user/PurchaseSuccess'
import Downloads from './pages/user/Downloads'
import Settings from './pages/user/Settings'
import Cart from './pages/Cart'

// Admin pages
import AdminLogin from './pages/admin/AdminLogin'
import AdminDashboard from './pages/admin/Dashboard'
import AdminDatasets from './pages/admin/DatasetsList'
import AdminDatasetCreate from './pages/admin/DatasetCreate'
import AdminPurchases from './pages/admin/PurchasesList'
import AdminUsers from './pages/admin/UsersList'

// Auth guard component
import { useAuthStore } from './store/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdminAuthenticated } = useAuthStore()
  
  if (!isAdminAuthenticated) {
    return <Navigate to="/admin/login" replace />
  }
  
  return <>{children}</>
}

export const router = createBrowserRouter([
  // Public routes with main layout
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Landing /> },
      { path: 'datasets', element: <Datasets /> },
      { path: 'datasets/:slug', element: <DatasetDetail /> },
      { path: 'privacy', element: <Privacy /> },
      { path: 'terms', element: <Terms /> },
      // Protected user routes
      { 
        path: 'cart', 
        element: <ProtectedRoute><Cart /></ProtectedRoute> 
      },
      { 
        path: 'checkout/:datasetId', 
        element: <ProtectedRoute><Checkout /></ProtectedRoute> 
      },
      { 
        path: 'purchase/success', 
        element: <ProtectedRoute><PurchaseSuccess /></ProtectedRoute> 
      },
      { 
        path: 'downloads', 
        element: <ProtectedRoute><Downloads /></ProtectedRoute> 
      },
      { 
        path: 'settings', 
        element: <ProtectedRoute><Settings /></ProtectedRoute> 
      },
    ],
  },
  // Auth routes
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <Login /> },
      { path: 'signup', element: <Signup /> },
    ],
  },
  // Admin routes
  {
    path: '/admin',
    children: [
      { path: 'login', element: <AdminLogin /> },
      {
        index: true,
        element: <AdminRoute><AdminDashboard /></AdminRoute>,
      },
      {
        path: 'datasets',
        element: <AdminRoute><AdminDatasets /></AdminRoute>,
      },
      {
        path: 'datasets/new',
        element: <AdminRoute><AdminDatasetCreate /></AdminRoute>,
      },
      {
        path: 'purchases',
        element: <AdminRoute><AdminPurchases /></AdminRoute>,
      },
      {
        path: 'users',
        element: <AdminRoute><AdminUsers /></AdminRoute>,
      },
    ],
  },
  // 404 Catch-all route
  {
    path: '*',
    element: <NotFound />,
  },
])