import { Outlet, Link, useLocation } from 'react-router-dom'
import useAuthStore from '../stores/authStore'
import './Layout.css'

function Layout() {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-brand">
            <Link to="/dashboard">Trading Platform</Link>
          </div>
          <div className="nav-links">
            <Link
              to="/dashboard"
              className={location.pathname === '/dashboard' ? 'active' : ''}
            >
              Dashboard
            </Link>
            <Link
              to="/profiles"
              className={location.pathname.startsWith('/profiles') ? 'active' : ''}
            >
              Profiles
            </Link>
          </div>
          <div className="nav-user">
            <span>{user?.email}</span>
            <button onClick={logout} className="btn-logout">
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

