import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { CheckCircle2, Download, ShieldCheck, ArrowRight, FileText, Anchor } from 'lucide-react'

export default function SuccessDossie() {
  const [searchParams] = useSearchParams()
  const [countdown, setCountdown] = useState(10)
  
  const ativoId = searchParams.get('ativo_id') || ''
  const nivel = searchParams.get('nivel') || 'compact'

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-[#010c20] text-white flex flex-col items-center justify-center p-6 font-['Inter']">
      <div className="max-w-md w-full text-center space-y-8 animate-in fade-in zoom-in duration-700">
        {/* Success Icon */}
        <div className="relative inline-block">
          <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full"></div>
          <div className="relative w-24 h-24 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={48} className="text-emerald-400" />
          </div>
        </div>

        {/* Text content */}
        <div className="space-y-3">
          <h1 className="text-3xl font-serif font-bold tracking-tight">Dossiê Certificado!</h1>
          <p className="text-white/40 text-sm leading-relaxed">
            O pagamento foi processado com sucesso. O <span className="text-[#c5a059] font-bold">Protocolo SHA-256</span> foi gerado e o dossiê imutável já está disponível.
          </p>
        </div>

        {/* Details Card */}
        <div className="bg-white/[0.02] border border-white/5 rounded-sm p-6 text-left space-y-4">
          <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-white/20">
            <span>Detalhes do Registro</span>
            <span className="text-[#c5a059]">ID: #{ativoId.slice(0,8).toUpperCase()}</span>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm text-white/60">
              <Anchor size={16} className="text-white/20" />
              <span>Nível: <span className="text-white capitalize">{nivel}</span></span>
            </div>
            <div className="flex items-center gap-3 text-sm text-white/60">
              <ShieldCheck size={16} className="text-emerald-500/50" />
              <span>Status: <span className="text-emerald-400 font-bold uppercase tracking-tighter">Imutável / Blockchain</span></span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-4 pt-4">
          <button 
            className="w-full bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all shadow-xl shadow-[#c5a059]/10"
          >
            <Download size={16} />
            Baixar Dossiê em PDF
          </button>
          
          <Link 
            to="/app/ativos"
            className="w-full flex items-center justify-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/30 hover:text-white transition-colors"
          >
            Voltar para Ativos
            <ArrowRight size={14} />
          </Link>
        </div>

        {/* Footer */}
        <div className="pt-8 border-t border-white/5 flex flex-col items-center gap-4">
          <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.4em] text-white/10">
            <FileText size={12} />
            Yachts Atlas Protocol v0.1
          </div>
          <p className="text-[9px] text-white/20 uppercase tracking-widest">
            Redirecionando em {countdown} segundos...
          </p>
        </div>
      </div>
    </div>
  )
}
