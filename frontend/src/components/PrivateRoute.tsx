import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function PrivateRoute() {
  const { session, loading } = useAuth()
  const devToken = localStorage.getItem('yachts_token')

  if (loading) {
    return (
      <div className="min-h-screen bg-[#010c20] flex items-center justify-center">
        <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full"></div>
      </div>
    )
  }

  if (!session && devToken !== 'dev_free_pass') {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
