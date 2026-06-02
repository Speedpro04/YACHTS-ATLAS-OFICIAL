import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { t } = useTranslation()

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 py-4 h-[var(--header-h)] flex items-center shadow-2xl overflow-hidden"
      style={{
        background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 70%)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}
    >
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#c5a059]/5 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-6 w-full flex items-center justify-between relative z-10">
        <Link to="/" className="group transition-all" aria-label="Yachts Atlas — Página inicial">
          <div className="w-[130px] md:w-[180px] relative">
             <img
               src="/logo-transparent.png"
               alt="Yachts Atlas — Custódia digital de ativos náuticos"
               className="w-full h-auto object-contain transition-transform group-hover:scale-105"
               width={180}
               height={60}
             />
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-10">
          <Link to="/" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
            {t('common.menu_home')}
          </Link>
          <Link to="/sobre" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
            {t('common.menu_about')}
          </Link>
          <Link to="/frota" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
            {t('common.menu_fleet')}
          </Link>
          <Link to="/seguranca" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
            {t('common.menu_security')}
          </Link>
          <Link to="/acesso-proprietario" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
            {t('common.menu_owner_portal')}
          </Link>
          <Link 
            to="/login" 
            className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-8 py-2.5 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-lg shadow-[#c5a059]/10"
          >
            {t('common.access_vault')}
          </Link>
        </nav>

        <button 
          className="md:hidden text-white"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-[#010c20] border-b border-white/5 p-8 flex flex-col gap-6 animate-in slide-in-from-top-4 duration-500 shadow-2xl">
           <Link to="/" className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_home')}</Link>
           <Link to="/sobre" className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_about')}</Link>
           <Link to="/frota" className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_fleet')}</Link>
           <Link to="/seguranca" className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_security')}</Link>
           <Link to="/acesso-proprietario" className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_owner_portal')}</Link>
           <Link 
            to="/login" 
            className="bg-[#c5a059] text-[#010c20] text-center py-4 rounded-sm text-xs font-black uppercase tracking-[0.2em] mt-4"
          >
            {t('common.access_vault')}
          </Link>
        </div>
      )}
    </header>
  )
}
