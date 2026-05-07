import { useState, useEffect } from 'react'
import { Anchor, User, Lock, ArrowRight, Shield, Sparkles } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function LoginArmador() {
  const navigate = useNavigate()
  const [embarcacao, setEmbarcacao] = useState('')
  const [cpf, setCpf] = useState('')
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [isFocused, setIsFocused] = useState<'embarcacao' | 'cpf' | 'pin' | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Formatador simples de CPF (XXX.XXX.XXX-XX)
  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '')
    if (value.length > 11) value = value.slice(0, 11)
    
    if (value.length > 9) value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
    else if (value.length > 6) value = value.replace(/(\d{3})(\d{3})(\d{3})/, '$1.$2.$3')
    else if (value.length > 3) value = value.replace(/(\d{3})(\d{3})/, '$1.$2')
    
    setCpf(value)
  }

  // Formatador para PIN (apenas números, máx 6 dígitos)
  const handlePinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '')
    if (value.length > 6) value = value.slice(0, 6)
    setPin(value)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    // Simulação de login para o protótipo
    setTimeout(() => {
      setLoading(false)
      // Como é o painel do armador, navegamos para a rota restrita
      navigate('/portal-armador')
    }, 1500)
  }

  return (
    <div className={`min-h-screen bg-[#012a4a] flex flex-col md:flex-row font-['Inter'] selection:bg-[#c5a059] selection:text-[#012a4a] ${mounted ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}>
      
      {/* Left Side: Branding */}
      <div 
        className="hidden lg:flex w-1/2 relative flex-col items-center justify-center p-20 overflow-hidden border-r border-white/5"
        style={{ background: 'radial-gradient(circle at center, #01497c 0%, #012a4a 100%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-sky-400/10 blur-[140px] rounded-full pointer-events-none animate-pulse"></div>

        <div className="relative z-10 flex flex-col items-center text-center">
          <Link to="/" className="group mb-12 block">
            <div className="relative">
              <div className="absolute inset-0 bg-[#c5a059]/20 blur-2xl rounded-full group-hover:blur-3xl transition-all duration-700"></div>
              <img 
                 src="/logo-transparent.png" 
                 alt="Yachts Atlas" 
                 className="w-[300px] h-auto object-contain transition-transform duration-700 group-hover:scale-105 relative z-10"
               />
            </div>
          </Link>

          <div className="max-w-md">
             <h2 className="text-[35px] font-serif font-bold text-white mb-4 tracking-tight leading-tight">
               Portal do <span className="italic text-[#c5a059]">Armador.</span>
             </h2>
             <div className="w-12 h-0.5 bg-[#c5a059]/40 mx-auto mb-6"></div>
             <p className="text-white/40 text-[15px] leading-relaxed font-light tracking-wide uppercase">
               Seu cofre digital privado. Acompanhe a integridade e o dossiê do seu ativo com total sigilo.
             </p>
          </div>

          <div className="mt-12 flex items-center gap-3 px-6 py-3 bg-white/5 border border-white/10 rounded-sm backdrop-blur-sm">
            <Shield size={16} className="text-[#c5a059]" />
            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-white/60">
              Acesso Criptografado & Isolado
            </span>
          </div>
        </div>

        <div className="absolute bottom-12 left-0 right-0 flex justify-center">
           <div className="flex items-center gap-2 text-white/10 text-[8px] font-black tracking-[0.5em] uppercase">
             <Sparkles size={12} />
             Protegido por Yachts Atlas
           </div>
        </div>
      </div>

      {/* Right Side: Login Form (3 Items) */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 md:px-24 xl:px-40 relative bg-[#012a4a] flex-1">
        
        {/* Mobile Header */}
        <div className="lg:hidden mb-12 flex flex-col items-center justify-center pt-10">
           <img src="/logo-transparent.png" alt="Logo" className="w-[180px] object-contain relative z-10 mb-6" />
           <p className="text-white/40 text-[10px] font-black uppercase tracking-[0.3em]">Portal do Armador</p>
        </div>

        <div className={`mb-12 ${mounted ? 'animate-in fade-in slide-in-from-right-8 duration-700' : ''}`}>
           <div className="flex items-center justify-between mb-4">
             <h3 className="text-white/40 text-[10px] font-black uppercase tracking-[0.4em] hidden lg:block">Proprietário</h3>
             <div className="bg-white/5 border border-white/10 rounded-sm p-1 ml-auto">
                <LanguageSwitcher />
             </div>
           </div>
           <h4 className="text-3xl font-serif font-bold text-white tracking-tight">Acesso ao Cofre</h4>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          
          {/* ITEM 1: Nome da Embarcação */}
          <div className={`space-y-2 group transition-all duration-300 ${isFocused === 'embarcacao' ? 'scale-[1.02]' : ''}`}>
            <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
              Nome da Embarcação
            </label>
            <div className="relative">
               <Anchor className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all duration-300 ${isFocused === 'embarcacao' ? 'text-[#c5a059] scale-110' : 'text-white/20'}`} size={18} />
               <input
                 type="text"
                 value={embarcacao}
                 onChange={(e) => setEmbarcacao(e.target.value)}
                 onFocus={() => setIsFocused('embarcacao')}
                 onBlur={() => setIsFocused(null)}
                 className={`w-full bg-white/5 border rounded-sm py-5 pl-12 pr-4 text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm font-medium ${
                   isFocused === 'embarcacao' 
                     ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]' 
                     : 'border-white/10 hover:border-white/20'
                 }`}
                 placeholder="Ex: Sea Explorer"
                 required
               />
            </div>
          </div>

          {/* ITEM 2: CPF */}
          <div className={`space-y-2 group transition-all duration-300 ${isFocused === 'cpf' ? 'scale-[1.02]' : ''}`}>
            <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
              CPF do Proprietário
            </label>
            <div className="relative">
               <User className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all duration-300 ${isFocused === 'cpf' ? 'text-[#c5a059] scale-110' : 'text-white/20'}`} size={18} />
               <input
                 type="text"
                 value={cpf}
                 onChange={handleCpfChange}
                 onFocus={() => setIsFocused('cpf')}
                 onBlur={() => setIsFocused(null)}
                 className={`w-full bg-white/5 border rounded-sm py-5 pl-12 pr-4 text-white outline-none transition-all duration-300 placeholder:text-white/10 text-sm font-medium tracking-widest ${
                   isFocused === 'cpf' 
                     ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]' 
                     : 'border-white/10 hover:border-white/20'
                 }`}
                 placeholder="000.000.000-00"
                 required
               />
            </div>
          </div>

          {/* ITEM 3: PIN */}
          <div className={`space-y-2 group transition-all duration-300 ${isFocused === 'pin' ? 'scale-[1.02]' : ''}`}>
            <label className="text-[10px] font-black uppercase tracking-widest text-white/40 group-focus-within:text-[#c5a059] transition-colors">
              PIN de Segurança
            </label>
            <div className="relative">
               <Lock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-all duration-300 ${isFocused === 'pin' ? 'text-[#c5a059] scale-110' : 'text-white/20'}`} size={18} />
               <input
                 type="password"
                 inputMode="numeric"
                 maxLength={6}
                 value={pin}
                 onChange={handlePinChange}
                 onFocus={() => setIsFocused('pin')}
                 onBlur={() => setIsFocused(null)}
                 className={`w-full bg-white/5 border rounded-sm py-5 pl-12 pr-4 text-[#c5a059] outline-none transition-all duration-300 placeholder:text-white/10 text-xl font-black tracking-[0.5em] ${
                   isFocused === 'pin' 
                     ? 'border-[#c5a059] bg-white/[0.08] shadow-[0_0_20px_rgba(197,160,89,0.1)]' 
                     : 'border-white/10 hover:border-white/20'
                 }`}
                 placeholder="••••"
                 required
               />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-5 mt-4 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 relative overflow-hidden ${
              loading 
                ? 'bg-[#c5a059]/50 cursor-not-allowed' 
                : 'bg-[#c5a059] hover:bg-[#b38f4d] shadow-2xl shadow-[#c5a059]/10 hover:shadow-[#c5a059]/20 hover:-translate-y-0.5 text-[#012a4a]'
            }`}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-[#012a4a] border-t-transparent rounded-full animate-spin"></div>
                Descriptografando Acesso...
              </>
            ) : (
              <>
                Acessar Ativo
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row gap-4 items-center justify-between text-[10px] text-white/20 uppercase tracking-widest font-bold">
           <span>Você é Marina ou Broker?</span>
           <Link to="/login" className="text-white/50 hover:text-white transition-all flex items-center gap-2 border border-white/10 px-4 py-2 rounded-sm bg-white/5">
             Ir para Gestão de Frota
           </Link>
        </div>
      </div>
    </div>
  )
}
