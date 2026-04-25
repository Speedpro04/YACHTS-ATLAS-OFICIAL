import { Outlet, Link, useLocation } from 'react-router-dom'
import { Home, Ship, FileText, User, LogOut } from 'lucide-react'

export default function Layout() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Início', icon: Home },
    { path: '/ativos', label: 'Ativos', icon: Ship },
    { path: '/documentos', label: 'Documentos', icon: FileText },
  ]
  
  const handleLogout = () => {
    localStorage.removeItem('yachts_token')
    window.location.href = '/login'
  }
  
  return (
    <div className="min-h-screen bg-navy-900">
      <nav className="bg-navy-800 border-b border-navy-800/50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-gold-500 to-gold-400 rounded-lg flex items-center justify-center">
                  <span className="text-navy-900 font-bold text-sm">YA</span>
                </div>
                <span className="text-white font-semibold text-lg">Yachts Atlas</span>
              </Link>
              
              <div className="hidden md:flex items-center gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                      location.pathname === item.path
                        ? 'bg-gold-500/20 text-gold-500'
                        : 'text-gray-400 hover:text-white hover:bg-navy-900/50'
                    }`}
                  >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                  </Link>
                ))}
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <button className="p-2 text-gray-400 hover:text-white transition-all">
                <User size={20} />
              </button>
              <button 
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-white transition-all"
                title="Sair"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
      
      <nav className="fixed bottom-0 left-0 right-0 bg-navy-800 border-t border-navy-800/50 md:hidden">
        <div className="flex items-center justify-around h-16">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-1 px-4 py-2 ${
                location.pathname === item.path ? 'text-gold-500' : 'text-gray-400'
              }`}
            >
              <item.icon size={20} />
              <span className="text-xs">{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  )
}