import { useState, useEffect } from 'react'
import { Lock, Mail, ArrowRight, Shield, Eye, EyeOff, Sparkles } from 'lucide-react'
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
  const [showPassword, setShowPassword] = useState(false)
  const [isFocused, setIsFocused] = useState<'email' | 'password' | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

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
    <div className={`min-h-screen bg-[#010c20] flex font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20] ${mounted ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}>
      {/* Left Side: Massive Branding - Centralized */}
      <div 
        className="hidden lg:flex w-1/2 relative flex-col items-center justify-center p-20 overflow-hidden border-r border-white/5"
        style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
      >
        {/* Spotlight lighting */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c5a059]/5 blur-[140px] rounded-full pointer-events-none animate-pulse"></div>

        {/* Floating particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-[#c5a059]/20 rounded-full animate-float"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${5 + Math.random() * 10}s`
              }}
            />
          ))}
        </div>

        <div className="relative z-10 flex flex-col items-center text-center">
          {/* Logo 300px */}
          <Link to="/" className="group mb-12 block">
            <div className="relative">
              <div className="absolute inset-0 bg-[#c5a059]/20 blur-2xl rounded-full group-hover:blur-3xl transition-all duration-700"></div>
              <img 
                 src="/logo-transparent.png" 
                 alt="Yachts Atlas" 
                 className="w-[380px] h-auto object-contain transition-transform duration-700 group-hover:scale-105 relative z-10"
               />
            </div>
          </Link>

          {/* Refined Small Text */}
          <div className="max-w-md">
             <h2 className="text-[35px] font-serif font-bold text-white mb-4 tracking-tight leading-tight">
               {t('auth.standard_title')}<span className="italic text-[#c5a059]">{t('auth.standard_highlight')}</span>
             </h2>
             <div className="w-12 h-0.5 bg-[#c5a059]/40 mx-auto mb-6"></div>
             <p className="text-white/40 text-[17px] leading-relaxed font-light tracking-wide uppercase">
               {t('auth.standard_desc')}
             </p>
          </div>

          {/* Security Badge */}
          <div className="mt-12 flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/10 rounded-sm backdrop-blur-sm">
            <Shield size={16} className="text-[#c5a059]" />
            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-white/60">
              {t('auth.encrypted_connection')}
            </span>
          </div>
        </div>

        {/* Protocol Badge - Bottom */}
        <div className="absolute bottom-12 left-0 right-0 flex justify-center">
           <div className="flex items-center gap-2 text-white/10 text-[8px] font-black tracking-[0.5em] uppercase">
             <Sparkles size={12} />
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
           <div className="relative mb-6">
             <div className="absolute inset-0 bg-[#c5a059]/20 blur-2xl rounded-full"></div>
             <img src="/logo-transparent.png" alt="Logo" className="w-[180px] object-contain relative z-10" />
           </div>
           <p className="text-white/40 text-[8px] font-black uppercase tracking-[0.3em]">{t('auth.personal_security')}</p>
        </div>

        <div className={`mb-12 ${mounted ? 'animate-in fade-in slide-in-from-right-8 duration-700' : ''}`}>
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
               <Shield size={14} />
               {error}
            </p>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div className={`space-y-2 group transition-all duration-300 ${isFocused === 'email' ? 'scale-[1.02]' : ''}`}>
            <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
              {t('auth.vault_email')}
            </label>
            <div className="relative">
               <Mail className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all duration-300 ${isFocused === 'email' ? 'text-[#c5a059] scale-110' : 'text-white/20'}`} size={18} />
               <input
                 type="email"
                 value={email}
                 onChange={(e) => setEmail(e.target.value)}
                 onFocus={() => setIsFocused('email')}
                 onBlur={() => setIsFocused(null)}
                 className={`w-full bg-white/5 border rounded-sm py-5 pl-12 pr-4 text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm ${
                   isFocused === 'email' 
                     ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]' 
                     : 'border-white/10 hover:border-white/20'
                 }`}
                 placeholder="admin@yachtatlas.com"
                 required
               />
               {email && (
                 <div className="absolute right-4 top-1/2 -translate-y-1/2">
                   <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                 </div>
               )}
            </div>
          </div>

          <div className={`space-y-2 group transition-all duration-300 ${isFocused === 'password' ? 'scale-[1.02]' : ''}`}>
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
                {t('auth.security_key')}
              </label>
              <a href="#" className="text-[9px] font-bold text-[#c5a059] uppercase tracking-widest hover:text-white transition-all">{t('auth.forgot_key')}</a>
            </div>
            <div className="relative">
               <Lock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all duration-300 ${isFocused === 'password' ? 'text-[#c5a059] scale-110' : 'text-white/20'}`} size={18} />
               <input
                 type={showPassword ? 'text' : 'password'}
                 value={password}
                 onChange={(e) => setPassword(e.target.value)}
                 onFocus={() => setIsFocused('password')}
                 onBlur={() => setIsFocused(null)}
                 className={`w-full bg-white/5 border rounded-sm py-5 pl-12 pr-12 text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm ${
                   isFocused === 'password' 
                     ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]' 
                     : 'border-white/10 hover:border-white/20'
                 }`}
                 placeholder="••••••••"
                 required
               />
               <button
                 type="button"
                 onClick={() => setShowPassword(!showPassword)}
                 className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-[#c5a059] transition-all"
               >
                 {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
               </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-5 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 relative overflow-hidden ${
              loading 
                ? 'bg-[#c5a059]/50 cursor-not-allowed' 
                : 'bg-[#c5a059] hover:bg-[#b38f4d] shadow-2xl shadow-[#c5a059]/10 hover:shadow-[#c5a059]/20 hover:-translate-y-0.5'
            }`}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-[#010c20] border-t-transparent rounded-full animate-spin"></div>
                {t('auth.decrypting')}
              </>
            ) : (
              <>
                {t('auth.open_vault')}
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-16 pt-8 border-t border-white/5 flex items-center justify-between text-[10px] text-white/20 uppercase tracking-widest font-bold">
           <span>{t('auth.no_account')}</span>
           <Link to="/registro-marina" className="text-[#c5a059] hover:text-white transition-all flex items-center gap-2">
             {t('auth.request_membership')}
             <ArrowRight size={14} />
           </Link>
        </div>
      </div>
    </div>
  )
}