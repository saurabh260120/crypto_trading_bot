import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './stores/authStore'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Profiles from './pages/Profiles'
import ProfileDetail from './pages/ProfileDetail'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="profiles" element={<Profiles />} />
        <Route path="profiles/:id" element={<ProfileDetail />} />
      </Route>
    </Routes>
  )
}

export default App

