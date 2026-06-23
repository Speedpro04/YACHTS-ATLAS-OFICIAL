import { useState, useEffect } from 'react'
import { Lock, ArrowRight, Shield, Eye, EyeOff, Sparkles, CheckCircle2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { supabase } from '../services/api'

export default function RedefinirSenha() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [isFocused, setIsFocused] = useState<'password' | 'confirm' | null>(null)
  const [ready, setReady] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Quando o usuário abre o link do e-mail, o Supabase cria a sessão de recuperação
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') setReady(true)
    })
    // Também cobre o caso em que a sessão já foi estabelecida antes do listener
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setReady(true)
    })
    return () => subscription.unsubscribe()
  }, [])

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError(t('auth.reset_too_short') || 'A nova chave deve ter ao menos 8 caracteres.')
      return
    }
    if (password !== confirm) {
      setError(t('auth.reset_mismatch') || 'As chaves não coincidem.')
      return
    }
    setLoading(true)
    try {
      const { error: updateError } = await supabase.auth.updateUser({ password })
      if (updateError) {
        setError(t('auth.reset_error') || 'Não foi possível redefinir. O link pode ter expirado.')
        return
      }
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2500)
    } catch (err) {
      setError(t('auth.reset_error') || 'Não foi possível redefinir. O link pode ter expirado.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const inputClass = (campo: string) =>
    `w-full bg-white/5 border rounded-sm py-5 pl-12 pr-12 text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm ${
      isFocused === campo
        ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]'
        : 'border-white/10 hover:border-white/20'
    }`

  return (
    <div className={`min-h-screen bg-[#010c20] flex items-center justify-center px-8 font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20] ${mounted ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c5a059]/5 blur-[140px] rounded-full pointer-events-none animate-pulse"></div>

      <div className="relative z-10 w-full max-w-md">
        <Link to="/" className="group mb-12 block text-center">
          <img src="/logo-transparent.png" alt="Yachts Atlas" className="w-[220px] h-auto object-contain mx-auto transition-transform duration-700 group-hover:scale-105" />
        </Link>

        <div className="mb-10 text-center">
          <h3 className="text-white/40 text-[10px] font-black uppercase tracking-[0.4em] mb-3">{t('auth.personal_security')}</h3>
          <h4 className="text-3xl font-serif font-bold text-white tracking-tight">{t('auth.reset_title')}</h4>
        </div>

        {success ? (
          <div className="bg-[#c5a059]/10 border border-[#c5a059]/50 p-8 rounded-sm text-center animate-in fade-in duration-500">
            <CheckCircle2 size={40} className="text-[#c5a059] mx-auto mb-4" />
            <p className="text-white text-sm font-light leading-relaxed mb-2">{t('auth.reset_success')}</p>
            <p className="text-white/40 text-[10px] font-black uppercase tracking-widest">{t('auth.reset_redirecting')}</p>
          </div>
        ) : (
          <>
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-sm mb-8 animate-in shake duration-300">
                <p className="text-red-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                  <Shield size={14} /> {error}
                </p>
              </div>
            )}

            {!ready && (
              <div className="bg-white/5 border border-white/10 p-4 rounded-sm mb-8">
                <p className="text-white/50 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                  <Sparkles size={14} /> {t('auth.reset_validating')}
                </p>
              </div>
            )}

            <form onSubmit={handleReset} className="space-y-6">
              <div className="space-y-2 group">
                <label className="text-[10px] font-black uppercase tracking-widest text-white/40">{t('auth.reset_new_key')}</label>
                <div className="relative">
                  <Lock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all ${isFocused === 'password' ? 'text-[#c5a059]' : 'text-white/20'}`} size={18} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setIsFocused('password')}
                    onBlur={() => setIsFocused(null)}
                    className={inputClass('password')}
                    placeholder="••••••••"
                    required
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-[#c5a059] transition-all">
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="space-y-2 group">
                <label className="text-[10px] font-black uppercase tracking-widest text-white/40">{t('auth.reset_confirm_key')}</label>
                <div className="relative">
                  <Lock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all ${isFocused === 'confirm' ? 'text-[#c5a059]' : 'text-white/20'}`} size={18} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    onFocus={() => setIsFocused('confirm')}
                    onBlur={() => setIsFocused(null)}
                    className={inputClass('confirm')}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !ready}
                className={`w-full py-5 mt-2 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 ${
                  loading || !ready ? 'bg-[#c5a059]/50 cursor-not-allowed text-[#010c20]/60' : 'bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] hover:-translate-y-0.5'
                }`}
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#010c20] border-t-transparent rounded-full animate-spin"></div>
                    {t('auth.reset_saving')}
                  </>
                ) : (
                  <>
                    {t('auth.reset_cta')}
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            <div className="mt-12 pt-8 border-t border-white/5 text-center">
              <Link to="/login" className="text-white/30 hover:text-[#c5a059] transition-colors text-[10px] font-black uppercase tracking-[0.2em]">
                ← {t('auth.reset_back_login')}
              </Link>
            </div>
          </>
        )}

        <div className="mt-12 flex items-center justify-center gap-2 text-white/10 text-[8px] font-black tracking-[0.5em] uppercase">
          <Sparkles size={12} /> {t('auth.authenticated_by')}
        </div>
      </div>
    </div>
  )
}
