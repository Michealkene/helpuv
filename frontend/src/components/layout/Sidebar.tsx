import { Link } from 'react-router-dom'

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r">
      <nav className="p-4">
        <Link to="/admin" className="block py-2 px-4 hover:bg-gray-100 rounded">
          Dashboard
        </Link>
        <Link to="/admin/datasets" className="block py-2 px-4 hover:bg-gray-100 rounded">
          Datasets
        </Link>
        <Link to="/admin/purchases" className="block py-2 px-4 hover:bg-gray-100 rounded">
          Purchases
        </Link>
        <Link to="/admin/users" className="block py-2 px-4 hover:bg-gray-100 rounded">
          Users
        </Link>
      </nav>
    </aside>
  )
}