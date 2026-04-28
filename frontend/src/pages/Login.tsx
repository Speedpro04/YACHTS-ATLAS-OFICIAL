import { useState } from 'react'
import { Lock, Mail, ArrowRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useTranslation } from 'react-i18next'

export default function Login() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const data = await api.auth.login(email, password)
      localStorage.setItem('yachts_token', data.access_token)
      navigate('/app')
    } catch (err) {
      setError(t('auth.error_credentials'))
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#010c20] flex font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      {/* Left Side: Massive Branding - Centralized */}
      <div 
        className="hidden lg:flex w-1/2 relative flex-col items-center justify-center p-20 overflow-hidden border-r border-white/5"
        style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
      >
        {/* Spotlight lighting */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c5a059]/5 blur-[140px] rounded-full pointer-events-none"></div>

        <div className="relative z-10 flex flex-col items-center text-center">
          {/* Logo 300px */}
          <Link to="/" className="group mb-12 block">
            <img 
               src="/logo-transparent.png" 
               alt="Yachts Atlas" 
               className="w-[380px] h-auto object-contain transition-transform duration-700 group-hover:scale-105"
             />
          </Link>

          {/* Refined Small Text - Increased by 5px */}
          <div className="max-w-md">
             <h2 className="text-[35px] font-serif font-bold text-white mb-4 tracking-tight leading-tight">
               {t('auth.standard_title')}<span className="italic text-[#c5a059]">{t('auth.standard_highlight')}</span>
             </h2>
             <div className="w-12 h-0.5 bg-[#c5a059]/40 mx-auto mb-6"></div>
             <p className="text-white/40 text-[17px] leading-relaxed font-light tracking-wide uppercase">
               {t('auth.standard_desc')}
             </p>
          </div>
        </div>

        {/* Protocol Badge - Bottom */}
        <div className="absolute bottom-12 left-0 right-0 flex justify-center">
           <div className="text-white/10 text-[8px] font-black tracking-[0.5em] uppercase">
             {t('auth.authenticated_by')}
           </div>
        </div>
      </div>

      {/* Right Side: Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 md:px-24 xl:px-40 relative bg-[#010c20]">
        {/* Mobile Header */}
        <div 
          className="lg:hidden mb-12 flex flex-col items-center justify-center p-12 rounded-2xl"
          style={{ background: 'radial-gradient(circle, #021a3d 0%, #010c20 100%)' }}
        >
           <img src="/logo-transparent.png" alt="Logo" className="w-[180px] object-contain mb-6" />
           <p className="text-white/40 text-[8px] font-black uppercase tracking-[0.3em]">{t('auth.personal_security')}</p>
        </div>

        <div className="mb-12">
           <div className="flex items-center justify-between mb-4">
             <h3 className="text-white/40 text-[10px] font-black uppercase tracking-[0.4em] hidden lg:block">{t('auth.personal_security')}</h3>
             <div className="bg-white/5 border border-white/10 rounded-sm p-1 ml-auto">
                <LanguageSwitcher />
             </div>
           </div>
           <h4 className="text-4xl font-serif font-bold text-white tracking-tight">{t('auth.secure_login')}</h4>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-sm mb-8 animate-in shake duration-300">
            <p className="text-red-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
               {error}
            </p>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2 group">
            <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
              {t('auth.vault_email')}
            </label>
            <div className="relative">
               <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-[#c5a059] transition-all" size={18} />
               <input
                 type="email"
                 value={email}
                 onChange={(e) => setEmail(e.target.value)}
                 className="w-full bg-white/5 border border-white/10 rounded-sm py-5 pl-12 pr-4 text-white focus:border-[#c5a059] focus:bg-white/[0.08] outline-none transition-all placeholder:text-white/10 text-sm"
                 placeholder="admin@yachtatlas.com"
                 required
               />
            </div>
          </div>

          <div className="space-y-2 group">
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
                {t('auth.security_key')}
              </label>
              <a href="#" className="text-[9px] font-bold text-[#c5a059] uppercase tracking-widest hover:text-white transition-all">{t('auth.forgot_key')}</a>
            </div>
            <div className="relative">
               <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-[#c5a059] transition-all" size={18} />
               <input
                 type="password"
                 value={password}
                 onChange={(e) => setPassword(e.target.value)}
                 className="w-full bg-white/5 border border-white/10 rounded-sm py-5 pl-12 pr-4 text-white focus:border-[#c5a059] focus:bg-white/[0.08] outline-none transition-all placeholder:text-white/10 text-sm"
                 placeholder="••••••••"
                 required
               />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-5 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 shadow-2xl shadow-[#c5a059]/10 disabled:opacity-50"
          >
            {loading ? t('auth.decrypting') : t('auth.open_vault')}
            <ArrowRight size={16} />
          </button>
        </form>

        <div className="mt-16 pt-8 border-t border-white/5 flex items-center justify-between text-[10px] text-white/20 uppercase tracking-widest font-bold">
           <span>{t('auth.no_account')}</span>
           <Link to="/signup" className="text-[#c5a059] hover:text-white transition-all">{t('auth.request_membership')}</Link>
        </div>
      </div>
    </div>
  )
}