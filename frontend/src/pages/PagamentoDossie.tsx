import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { 
  Shield, Download, CheckCircle2, AlertCircle, Lock, 
  FileCheck, ArrowLeft, ExternalLink, Zap, Award
} from 'lucide-react'
import { api } from '../services/api'
import { useTranslation } from 'react-i18next'

type NivelDossie = 'compact' | 'executive' | 'superyacht'

const PRECOS = {
  compact:    { valor: 200, label: 'Compacto', descricao: 'Até 45 pés', color: 'text-blue-400', border: 'border-blue-400/20', bg: 'bg-blue-400/5' },
  executive:  { valor: 400, label: 'Executivo', descricao: '46 a 79 pés', color: 'text-[#c5a059]', border: 'border-[#c5a059]/20', bg: 'bg-[#c5a059]/5' },
  superyacht: { valor: 600, label: 'Superyacht', descricao: '80 pés ou mais', color: 'text-purple-400', border: 'border-purple-400/20', bg: 'bg-purple-400/5' },
}

export default function PagamentoDossie() {
  const { } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  
  const ativoId = searchParams.get('ativo_id') || ''
  const nivelParam = (searchParams.get('nivel') || 'compact') as NivelDossie
  
  const [nivelSelecionado, setNivelSelecionado] = useState<NivelDossie>(nivelParam)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  
  const preco = PRECOS[nivelSelecionado]
  const splitMarina = preco.valor / 2
  const splitPlataforma = preco.valor / 2

  const handlePagar = async () => {
    setLoading(true)
    setErro('')
    try {
      const successUrl = `${window.location.origin}/app/dossie-sucesso?ativo_id=${ativoId}&nivel=${nivelSelecionado}`
      const cancelUrl = `${window.location.origin}/app/ativos`

      const sessao = await api.pagamentos.checkoutDossie({
        dossier_level: nivelSelecionado,
        ativo_id: ativoId,
        success_url: successUrl,
        cancel_url: cancelUrl,
      })

      // Redirecionar para a página de pagamento da Stripe
      if (sessao?.url) {
        window.location.href = sessao.url
      } else {
        setErro('Não foi possível iniciar o pagamento. Tente novamente.')
      }
    } catch (err: any) {
      setErro(err.message || 'Erro ao processar pagamento.')
    } finally {
      setLoading(false)
    }
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
          {/* Seleção de Nível */}
          <div className="lg:col-span-3 space-y-6">
            <h2 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 mb-6">Selecione o Nível do Dossiê</h2>
            
            {(Object.entries(PRECOS) as [NivelDossie, typeof PRECOS[NivelDossie]][]).map(([nivel, info]) => (
              <button
                key={nivel}
                onClick={() => setNivelSelecionado(nivel)}
                className={`w-full text-left p-6 rounded-sm border transition-all duration-300 group ${
                  nivelSelecionado === nivel
                    ? `${info.border} ${info.bg}`
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      nivelSelecionado === nivel ? `border-[#c5a059] bg-[#c5a059]` : 'border-white/20'
                    }`}>
                      {nivelSelecionado === nivel && <div className="w-2 h-2 rounded-full bg-[#010c20]"></div>}
                    </div>
                    <div>
                      <span className={`block text-sm font-black uppercase tracking-[0.2em] ${nivelSelecionado === nivel ? info.color : 'text-white/60'}`}>
                        {info.label}
                      </span>
                      <span className="block text-[10px] text-white/30 uppercase tracking-widest mt-0.5">{info.descricao}</span>
                    </div>
                  </div>
                  <span className={`text-2xl font-serif font-bold ${nivelSelecionado === nivel ? info.color : 'text-white/30'}`}>
                    US$ {info.valor}
                  </span>
                </div>

                {/* Itens inclusos */}
                <div className="grid grid-cols-2 gap-2 mt-4 pl-9">
                  {[
                    'Histórico completo de manutenção',
                    'Documentação certificada',
                    'Fotos com timestamp',
                    'Trilha de auditoria SHA-256',
                    'Assinatura digital',
                    nivel === 'superyacht' ? 'Compliance internacional' : nivel === 'executive' ? 'Laudos técnicos' : 'Relatório básico',
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <CheckCircle2 size={12} className={nivelSelecionado === nivel ? 'text-emerald-500' : 'text-white/10'} />
                      <span className="text-[10px] text-white/40">{item}</span>
                    </div>
                  ))}
                </div>
              </button>
            ))}

            {/* Aviso Split */}
            <div className="flex items-start gap-4 p-5 rounded-sm border border-[#c5a059]/10 bg-[#c5a059]/5">
              <Award size={20} className="text-[#c5a059] flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-1">Divisão de Receita 50/50</p>
                <p className="text-[11px] text-white/40 leading-relaxed">
                  A marina que gerencia este ativo recebe automaticamente <strong className="text-white/60">US$ {splitMarina}</strong> via Stripe Connect. 
                  Você paga uma vez, a plataforma distribui em tempo real.
                </p>
              </div>
            </div>
          </div>

          {/* Resumo e Pagamento */}
          <div className="lg:col-span-2">
            <div className="sticky top-8 space-y-6">
              {/* Card Resumo */}
              <div className="bg-white/[0.02] border border-white/5 rounded-sm overflow-hidden">
                <div className="p-6 border-b border-white/5">
                  <h3 className="text-xs font-black uppercase tracking-[0.3em] text-white/30 mb-4">Resumo do Pedido</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-white/60">Dossiê {PRECOS[nivelSelecionado].label}</span>
                      <span className="text-sm font-bold text-white">US$ {preco.valor}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/30">Repasse à marina (50%)</span>
                      <span className="text-emerald-500/70">− US$ {splitMarina}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/30">Plataforma Yachts Atlas (50%)</span>
                      <span className="text-white/30">− US$ {splitPlataforma}</span>
                    </div>
                  </div>
                </div>

                <div className="p-6 border-b border-white/5 bg-white/[0.01]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black uppercase tracking-widest text-white/40">Total a Pagar</span>
                    <span className="text-3xl font-serif font-bold text-[#c5a059]">US$ {preco.valor}</span>
                  </div>
                  <p className="text-[9px] text-white/20 mt-2 uppercase tracking-widest">Pagamento único • Sem recorrência</p>
                </div>

                <div className="p-6 space-y-4">
                  {erro && (
                    <div className="flex items-center gap-3 p-4 rounded-sm bg-rose-500/10 border border-rose-500/20">
                      <AlertCircle size={16} className="text-rose-250 flex-shrink-0" />
                      <p className="text-xs text-rose-300">{erro}</p>
                    </div>
                  )}

                  <button
                    onClick={handlePagar}
                    disabled={loading}
                    className="w-full bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 disabled:cursor-not-allowed text-[#010c20] py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all shadow-xl shadow-[#c5a059]/10"
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-[#010c20] border-t-transparent rounded-full animate-spin"></div>
                        Redirecionando para o Stripe...
                      </>
                    ) : (
                      <>
                        <Download size={16} />
                        Pagar e Gerar Dossiê
                        <ExternalLink size={14} />
                      </>
                    )}
                  </button>

                  {/* Garantias */}
                  <div className="space-y-3 pt-2">
                    {[
                      { icon: Lock, texto: 'Pagamento 100% seguro via Stripe' },
                      { icon: Shield, texto: 'Dados protegidos por criptografia SHA-256' },
                      { icon: Zap, texto: 'Dossiê disponível imediatamente após pagamento' },
                    ].map(({ icon: Icon, texto }, i) => (
                      <div key={i} className="flex items-center gap-3 text-[10px] text-white/20">
                        <Icon size={14} className="text-white/20 flex-shrink-0" />
                        {texto}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Badge Stripe */}
              <div className="flex items-center justify-center gap-3 opacity-40">
                <Lock size={12} />
                <span className="text-[9px] uppercase tracking-widest text-white/50 font-black">Processado com segurança pela Stripe</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
