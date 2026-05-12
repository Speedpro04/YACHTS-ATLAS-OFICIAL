import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { CheckCircle2, Shield, ArrowRight, LayoutDashboard, Anchor, Lock } from 'lucide-react'

export default function SuccessOnboarding() {
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(15)

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          // Redirecionar para o dashboard após o countdown
          navigate('/app')
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [navigate])

  return (
    <div className="min-h-screen bg-[#010c20] text-white flex flex-col items-center justify-center p-6 font-['Inter']">
      <div className="max-w-xl w-full text-center space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
        
        {/* Branding */}
        <div className="flex flex-col items-center">
          <img src="/logo-transparent.png" alt="Yachts Atlas" className="h-12 mb-12 opacity-80" />
          
          <div className="relative">
            <div className="absolute inset-0 bg-[#c5a059]/20 blur-[100px] rounded-full"></div>
            <div className="relative w-20 h-20 bg-[#c5a059]/10 border border-[#c5a059]/30 rounded-full flex items-center justify-center mb-8">
              <Shield size={32} className="text-[#c5a059]" />
            </div>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight mb-4">
            Bem-vindo à <span className="text-[#c5a059] italic">Elite.</span>
          </h1>
          <p className="text-white/40 text-lg font-light max-w-md mx-auto leading-relaxed">
            Sua marina agora faz parte da rede Yachts Atlas. A gestão da sua frota acaba de entrar na era da imutabilidade.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { icon: Anchor, title: 'Frota Ilimitada', desc: 'Gerencie ativos' },
            { icon: Lock, title: 'Cofre Seguro', desc: 'Docs cripto' },
            { icon: CheckCircle2, title: 'Split Ativo', desc: '50% de receita' }
          ].map((item, i) => (
            <div key={i} className="bg-white/[0.02] border border-white/5 p-5 rounded-sm text-left">
              <item.icon size={20} className="text-[#c5a059] mb-3" />
              <p className="text-[10px] font-black uppercase tracking-widest text-white mb-1">{item.title}</p>
              <p className="text-[9px] text-white/30 uppercase tracking-tighter">{item.desc}</p>
            </div>
          ))}
        </div>

        {/* Primary Action */}
        <div className="pt-6 space-y-4">
          <Link 
            to="/app"
            className="w-full bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-5 rounded-sm text-xs font-black uppercase tracking-[0.4em] flex items-center justify-center gap-4 transition-all shadow-2xl shadow-[#c5a059]/10"
          >
            <LayoutDashboard size={18} />
            Acessar Dashboard
            <ArrowRight size={16} />
          </Link>
          
          <p className="text-[10px] text-white/20 uppercase tracking-[0.3em] font-black">
            Iniciando protocolo em {countdown} segundos...
          </p>
        </div>

      </div>
    </div>
  )
}
