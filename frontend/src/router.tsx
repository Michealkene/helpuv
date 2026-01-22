import { createBrowserRouter } from 'react-router-dom'
import Layout from './components/layout/Layout'
import AuthLayout from './components/layout/AuthLayout'

// Public pages
import Landing from './pages/public/Landing'
import Privacy from './pages/public/Privacy'
import Terms from './pages/public/Terms'

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

// Admin pages
import AdminDashboard from './pages/admin/Dashboard'
import AdminDatasets from './pages/admin/DatasetsList'
import AdminDatasetCreate from './pages/admin/DatasetCreate'
import AdminPurchases from './pages/admin/PurchasesList'
import AdminUsers from './pages/admin/UsersList'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Landing /> },
      { path: 'privacy', element: <Privacy /> },
      { path: 'terms', element: <Terms /> },
      { path: 'datasets', element: <Datasets /> },
      { path: 'datasets/:slug', element: <DatasetDetail /> },
      { path: 'checkout/:datasetId', element: <Checkout /> },
      { path: 'purchase/success', element: <PurchaseSuccess /> },
      { path: 'downloads', element: <Downloads /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <Login /> },
      { path: 'signup', element: <Signup /> },
    ],
  },
  {
    path: '/admin',
    element: <Layout />,
    children: [
      { index: true, element: <AdminDashboard /> },
      { path: 'datasets', element: <AdminDatasets /> },
      { path: 'datasets/new', element: <AdminDatasetCreate /> },
      { path: 'purchases', element: <AdminPurchases /> },
      { path: 'users', element: <AdminUsers /> },
    ],
  },
])