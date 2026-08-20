import { useState, useEffect } from 'react'
import { Mail, KeyRound, ArrowLeft, ArrowRight, Shield, Sparkles, Loader2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api, supabase } from '../services/api'

type Etapa = 'email' | 'codigo'

export default function LoginProprietario() {
  const navigate = useNavigate()
  const [etapa, setEtapa] = useState<Etapa>('email')
  const [email, setEmail] = useState('')
  const [codigo, setCodigo] = useState('')
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const [foco, setFoco] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  // Etapa 1: o armador digita o e-mail. O código sai por e-mail E WhatsApp.
  // Ele nunca cria senha — não há nada para esquecer, e o segredo passa a ser
  // a caixa dele, que é a única coisa que só ele tem.
  const handleEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErro('')
    try {
      await api.owner.codigo(email.trim())
      setEtapa('codigo')
    } catch {
      setErro('Não foi possível enviar o código. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // Etapa 2: o código é validado pelo próprio Supabase — a segurança continua
  // sendo dele; a gente só escolheu o carteiro.
  const handleCodigo = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErro('')
    try {
      const { error } = await supabase.auth.verifyOtp({
        email: email.trim(),
        token: codigo.trim(),
        type: 'email',
      })
      if (error) {
        setErro('Código inválido ou expirado. Peça um novo.')
        return
      }
      navigate('/portal-proprietario')
    } catch {
      setErro('Não foi possível verificar. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const voltarParaEmail = () => {
    setCodigo('')
    setErro('')
    setEtapa('email')
  }

  const inputClass = (campo: string, comOlho = false) =>
    `w-full bg-white/5 border rounded-sm py-5 pl-12 ${comOlho ? 'pr-12' : 'pr-4'} text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm ${
      foco === campo
        ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]'
        : 'border-white/10 hover:border-white/20'
    }`


  return (
    <div className={`min-h-screen bg-[#010c20] flex flex-col md:flex-row font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20] ${mounted ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}>
      {/* Branding */}
      <div
        className="hidden lg:flex w-1/2 relative flex-col items-center justify-center p-20 overflow-hidden border-r border-white/5"
        style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c5a059]/5 blur-[140px] rounded-full pointer-events-none animate-pulse"></div>
        <div className="relative z-10 flex flex-col items-center text-center">
          <Link to="/" className="group mb-12 block">
            <div className="relative">
              <div className="absolute inset-0 bg-[#c5a059]/20 blur-2xl rounded-full group-hover:blur-3xl transition-all duration-700"></div>
              <img src="/logo-transparent.png" alt="Yachts Atlas" className="w-[300px] h-auto object-contain transition-transform duration-700 group-hover:scale-105 relative z-10" />
            </div>
          </Link>
          <div className="max-w-md">
            <h2 className="text-[35px] font-serif font-bold text-white mb-4 tracking-tight leading-tight">
              Portal do <span className="italic text-[#c5a059]">Proprietário.</span>
            </h2>
            <div className="w-12 h-0.5 bg-[#c5a059]/40 mx-auto mb-6"></div>
            <p className="text-white/40 text-[15px] leading-relaxed font-light tracking-wide uppercase">
              Seu cofre digital privado. Acesse o dossiê do seu ativo com total sigilo.
            </p>
          </div>
          <div className="mt-12 flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/10 rounded-sm backdrop-blur-sm">
            <Shield size={16} className="text-[#c5a059]" />
            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-white/60">Acesso em Camadas</span>
          </div>
        </div>
        <div className="absolute bottom-12 left-0 right-0 flex justify-center">
          <div className="flex items-center gap-2 text-white/10 text-[8px] font-black tracking-[0.5em] uppercase">
            <Sparkles size={12} /> Protegido por Yachts Atlas
          </div>
        </div>
      </div>

      {/* Formulário */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 md:px-24 xl:px-40 relative bg-[#010c20] flex-1">
        <button onClick={() => navigate(-1)} className="absolute top-8 left-8 flex items-center gap-2 text-white/40 hover:text-[#c5a059] transition-all duration-300 group">
          <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Voltar</span>
        </button>

        <div className="lg:hidden mb-12 flex flex-col items-center justify-center pt-10">
          <img src="/logo-transparent.png" alt="Logo" className="w-[180px] object-contain relative z-10 mb-6" />
          <p className="text-white/40 text-[12px] font-black uppercase tracking-[0.3em]">Portal do Proprietário</p>
        </div>

        {/* Indicador de etapa */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <span className={`h-1 flex-1 rounded-full transition-all ${etapa === 'email' ? 'bg-[#c5a059]' : 'bg-[#c5a059]/40'}`}></span>
            <span className={`h-1 flex-1 rounded-full transition-all ${etapa === 'codigo' ? 'bg-[#c5a059]' : 'bg-white/10'}`}></span>
          </div>
          <h3 className="text-white/40 text-[10px] font-black uppercase tracking-[0.4em]">
            {etapa === 'email' ? 'Etapa 1 de 2 — Seu e-mail' : 'Etapa 2 de 2 — Código de acesso'}
          </h3>
          <h4 className="text-3xl font-serif font-bold text-white tracking-tight mt-2">
            {etapa === 'email' ? 'Acesso ao Cofre' : 'Confirme sua identidade'}
          </h4>
        </div>

        {erro && (
          <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-sm mb-8">
            <p className="text-red-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
              <Shield size={14} /> {erro}
            </p>
          </div>
        )}

        {etapa === 'email' ? (
          <form onSubmit={handleEmail} className="space-y-6">
            <p className="text-white/40 text-sm font-light leading-relaxed -mt-4 mb-2">
              Informe o e-mail cadastrado pela sua marina. Enviamos um código de acesso
              por e-mail e WhatsApp — sem senha para criar nem lembrar.
            </p>
            <div className="space-y-2 group">
              <label className="text-[10px] font-black uppercase tracking-widest text-white/40">E-mail</label>
              <div className="relative">
                <Mail className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all ${foco === 'email' ? 'text-[#c5a059]' : 'text-white/20'}`} size={18} />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} onFocus={() => setFoco('email')} onBlur={() => setFoco(null)} className={inputClass('email')} placeholder="seu@email.com" required autoFocus />
              </div>
            </div>
            <button type="submit" disabled={loading} className={`w-full py-5 mt-4 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 ${loading ? 'bg-[#c5a059]/50 cursor-not-allowed' : 'bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] hover:-translate-y-0.5'}`}>
              {loading ? <><Loader2 size={16} className="animate-spin" /> Enviando...</> : <>Receber Código <ArrowRight size={16} /></>}
            </button>
          </form>
        ) : (
          <form onSubmit={handleCodigo} className="space-y-6">
            <p className="text-white/40 text-sm font-light leading-relaxed -mt-4 mb-2">
              Enviamos um código para <span className="text-[#c5a059]">{email}</span> e para o
              seu WhatsApp. Ele vale por poucos minutos.
            </p>
            <div className="space-y-2 group">
              <label className="text-[10px] font-black uppercase tracking-widest text-white/40">Código de Acesso</label>
              <div className="relative">
                <KeyRound className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all ${foco === 'codigo' ? 'text-[#c5a059]' : 'text-white/20'}`} size={18} />
                <input
                  type="text" inputMode="numeric" autoComplete="one-time-code"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ''))}
                  onFocus={() => setFoco('codigo')} onBlur={() => setFoco(null)}
                  className={`${inputClass('codigo')} tracking-[0.5em] text-center text-lg`}
                  placeholder="000000" required autoFocus
                />
              </div>
            </div>
            <button type="submit" disabled={loading} className={`w-full py-5 mt-4 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 ${loading ? 'bg-[#c5a059]/50 cursor-not-allowed' : 'bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] hover:-translate-y-0.5'}`}>
              {loading ? <><Loader2 size={16} className="animate-spin" /> Abrindo cofre...</> : <>Acessar Meu Ativo <ArrowRight size={16} /></>}
            </button>
            <button type="button" onClick={voltarParaEmail} className="w-full text-[10px] font-black uppercase tracking-[0.2em] text-white/30 hover:text-[#c5a059] transition-colors">
              ← Usar outro e-mail
            </button>
          </form>
        )}

        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row gap-4 items-center justify-between text-[10px] text-white/20 uppercase tracking-widest font-bold">
          <span>É Marina ou Broker?</span>
          <Link to="/login" className="text-white/50 hover:text-white transition-all flex items-center gap-2 border border-white/10 px-4 py-2 rounded-sm bg-white/5">
            Ir para Gestão de Frota
          </Link>
        </div>
      </div>
    </div>
  )
}
