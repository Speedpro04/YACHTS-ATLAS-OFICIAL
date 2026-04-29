import { Outlet, Link, useLocation } from 'react-router-dom'
import { Home, Ship, FileText, LogOut, Bell, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from './LanguageSwitcher'

export default function Layout() {
  const location = useLocation()
  const { t } = useTranslation()
  
  const navItems = [
    { path: '/app', label: t('common.dashboard'), icon: Home },
    { path: '/app/ativos', label: t('common.assets'), icon: Ship },
    { path: '/app/documentos', label: t('dossier.level_3'), icon: FileText },
    { path: '/app/parceiros', label: t('common.partners'), icon: Users },
  ]
  
  const handleLogout = () => {
    localStorage.removeItem('yachts_token')
    window.location.href = '/'
  }
  
  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      {/* Sidebar - Desktop */}
      <aside 
        className="fixed left-0 top-0 bottom-0 w-28 border-r border-white/5 hidden lg:flex flex-col items-center py-8 z-50 shadow-2xl"
        style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
      >
        <Link to="/" className="mb-12 group transition-all">
          <img 
             src="/logo-transparent.png" 
             alt="Logo" 
             className="w-full h-auto object-contain px-4 group-hover:scale-110 transition-transform duration-500" 
           />
        </Link>

        <nav className="flex-1 flex flex-col gap-8">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`p-4 rounded-xl transition-all group relative ${
                location.pathname === item.path
                  ? 'text-[#c5a059]'
                  : 'text-white/40 hover:text-white hover:bg-white/5'
              }`}
            >
              <item.icon size={26} strokeWidth={1.5} />
              <span className="absolute left-full ml-4 px-2 py-1 bg-[#c5a059] text-[#010c20] text-[10px] font-black uppercase tracking-widest rounded opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap z-50 shadow-2xl">
                {item.label}
              </span>
              {location.pathname === item.path && (
                <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-[#c5a059] rounded-r-full shadow-[0_0_15px_#c5a059]"></div>
              )}
            </Link>
          ))}
        </nav>

        <div className="flex flex-col gap-6 mt-auto pt-8 border-t border-white/5 w-full items-center">
          <button className="text-white/40 hover:text-[#c5a059] transition-all relative group">
            <Bell size={24} strokeWidth={1.5} />
            <div className="absolute top-0 right-0 w-2 h-2 bg-[#c5a059] rounded-full border-2 border-[#010c20]"></div>
          </button>
          <button 
            onClick={handleLogout}
            className="text-white/40 hover:text-red-400 transition-all group relative mb-4"
          >
            <LogOut size={24} strokeWidth={1.5} />
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="lg:ml-28 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="h-24 border-b border-white/5 px-10 flex items-center justify-between bg-[#010c20]/90 backdrop-blur-xl sticky top-0 z-40">
          <div className="lg:hidden flex items-center gap-4">
             <img src="/logo-transparent.png" alt="Logo" className="w-[120px] object-contain" />
          </div>

          <div className="hidden lg:block">
            <div className="flex items-center gap-4">
               <div className="w-1.5 h-1.5 rounded-full bg-[#c5a059] animate-pulse"></div>
               <h2 className="text-[10px] font-black uppercase tracking-[0.5em] text-white/40">
                 System Protocol <span className="text-[#c5a059] mx-3">•</span> 
                 <span className="text-white">{navItems.find(i => i.path === location.pathname)?.label || 'Overview'}</span>
               </h2>
            </div>
          </div>

          <div className="flex items-center gap-8">
            <div className="bg-white/5 border border-white/10 rounded-sm p-1 shadow-inner">
               <LanguageSwitcher />
            </div>
            <div className="h-10 w-px bg-white/10 hidden sm:block"></div>
            <div className="hidden sm:flex items-center gap-4">
              <div className="text-right">
                <p className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Yacht Master</p>
                <p className="text-[8px] text-[#c5a059] uppercase tracking-[0.3em] font-bold">Premium Vault Access</p>
              </div>
              <div className="w-12 h-12 rounded-sm bg-gradient-to-br from-[#c5a059] to-[#010c20] border border-white/10 flex items-center justify-center font-black text-[#010c20] text-xs shadow-xl group cursor-pointer hover:scale-105 transition-transform">
                YM
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-12 flex-1 relative">
           {/* Subtle background glow */}
           <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-[#c5a059]/5 blur-[150px] rounded-full pointer-events-none"></div>
          <Outlet />
        </main>
      </div>

      {/* Bottom Nav - Mobile */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[#010c20] border-t border-white/5 h-20 px-4 flex items-center justify-around lg:hidden z-50 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center gap-1 transition-all ${
              location.pathname === item.path ? 'text-[#c5a059]' : 'text-white/40'
            }`}
          >
            <item.icon size={20} />
            <span className="text-[8px] font-black uppercase tracking-[0.2em]">{item.label}</span>
          </Link>
        ))}
        <button onClick={handleLogout} className="flex flex-col items-center gap-1 text-white/40">
          <LogOut size={20} />
          <span className="text-[8px] font-black uppercase tracking-[0.2em]">{t('lp.terms')}</span>
        </button>
      </nav>
    </div>
  )
}