import { useSearchParams, useNavigate } from 'react-router-dom'
import {
  Shield, Download, CheckCircle2, Lock,
  FileCheck, ArrowLeft, ExternalLink, Zap
} from 'lucide-react'
import { faixaPorPes, formatarPreco } from '../config/precosDossie'

const INCLUSOS = [
  'Identificação e procedência',
  'Histórico de propriedade',
  'Documentação certificada',
  'Histórico de manutenção e motorização',
  'Registro fotográfico (datado e geolocalizado)',
  'Laudos de terceiros custodiados',
  'Trilha de integridade SHA-256',
  'Assinatura digital verificável',
]

export default function PagamentoDossie() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const pes = Number(searchParams.get('pes')) || 0
  const faixa = faixaPorPes(pes)
  const precoFmt = formatarPreco(faixa.precoUSD)

  const handlePagar = () => {
    window.location.href = faixa.stripeLink
  }

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter']">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-5 flex items-center justify-between max-w-7xl mx-auto">
        <button
          onClick={() => navigate('/app/ativos')}
          className="flex items-center gap-3 text-white/40 hover:text-[#c5a059] transition-colors text-[10px] font-black uppercase tracking-widest"
        >
          <ArrowLeft size={16} />
          Voltar aos Ativos
        </button>
        <img src="/logo-transparent.png" alt="Yachts Atlas" className="h-8 opacity-70" />
      </div>

      <div className="max-w-5xl mx-auto px-6 py-16">
        {/* Título */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#c5a059]/30 bg-[#c5a059]/5 mb-6">
            <FileCheck size={14} className="text-[#c5a059]" />
            <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">Dossiê de Integridade</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-4">
            Emitir Dossiê <span className="text-[#c5a059] italic">Certificado</span>
          </h1>
          <p className="text-white/40 text-lg font-light max-w-xl mx-auto leading-relaxed">
            Documento auditável com trilha criptográfica completa. Válido para venda, seguro e transferência de propriedade.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-10">
          {/* Esquerda: o dossiê único + o que reúne */}
          <div className="lg:col-span-3 space-y-8">
            <div className="p-6 rounded-sm border border-[#c5a059]/20 bg-[#c5a059]/5">
              <div className="flex items-center justify-between">
                <div>
                  <span className="block text-sm font-black uppercase tracking-[0.2em] text-[#c5a059]">Dossiê Yachts Atlas</span>
                  <span className="block text-[10px] text-white/30 uppercase tracking-widest mt-1">Porte do ativo: {faixa.label}</span>
                </div>
                <span className="text-3xl font-serif font-bold text-[#c5a059]">{precoFmt}</span>
              </div>
              <p className="text-[11px] text-white/40 leading-relaxed mt-4">
                Um único dossiê, sempre completo. O preço acompanha o porte do ativo — da lancha ao megayacht.
              </p>
            </div>

            <div>
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 mb-6">O que o dossiê reúne</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {INCLUSOS.map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <CheckCircle2 size={14} className="text-emerald-500 flex-shrink-0" />
                    <span className="text-[11px] text-white/50">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Direita: resumo e pagamento */}
          <div className="lg:col-span-2">
            <div className="sticky top-8 space-y-6">
              <div className="bg-white/[0.02] border border-white/5 rounded-sm overflow-hidden">
                <div className="p-6 border-b border-white/5">
                  <h3 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 mb-4">Resumo do Pedido</h3>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white/60">Dossiê — {faixa.label}</span>
                    <span className="text-sm font-bold text-white">{precoFmt}</span>
                  </div>
                </div>

                <div className="p-6 border-b border-white/5 bg-white/[0.01]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black uppercase tracking-widest text-white/40">Total a Pagar</span>
                    <span className="text-3xl font-serif font-bold text-[#c5a059]">{precoFmt}</span>
                  </div>
                  <p className="text-[9px] text-white/20 mt-2 uppercase tracking-widest">Pagamento único • Sem recorrência</p>
                </div>

                <div className="p-6 space-y-4">
                  <button
                    onClick={handlePagar}
                    className="w-full bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all shadow-xl shadow-[#c5a059]/10"
                  >
                    <Download size={16} />
                    Pagar e Gerar Dossiê
                    <ExternalLink size={14} />
                  </button>

                  <div className="space-y-3 pt-2">
                    {[
                      { icon: Lock, texto: 'Pagamento 100% seguro via Stripe' },
                      { icon: Shield, texto: 'Integridade garantida por SHA-256' },
                      { icon: Zap, texto: 'Acesso ao dossiê após a confirmação' },
                    ].map(({ icon: Icon, texto }, i) => (
                      <div key={i} className="flex items-center gap-3 text-[10px] text-white/20">
                        <Icon size={14} className="text-white/20 flex-shrink-0" />
                        {texto}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-3 opacity-40">
                <Lock size={12} />
                <span className="text-[9px] uppercase tracking-widest text-white/50 font-black">Processado com segurança pela Stripe</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-white/5 py-8 text-center">
        <p className="text-[8px] text-white/15 uppercase tracking-[0.3em]">
          Desenvolvido pela{' '}
          <a
            href="https://axoshub.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-white/30 hover:text-[#c5a059] font-bold transition-all"
          >
            AXOS HUB
          </a>{' '}
          — Arquitetura Digital
        </p>
      </div>
    </div>
  )
}
