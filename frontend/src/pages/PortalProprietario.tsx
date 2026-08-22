import { useState, useEffect } from 'react'
import { Shield, FileCheck, Anchor, CheckCircle2, Wrench } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Ativo } from '../types'
import AtivoHub from '../components/AtivoHub'

export default function PortalProprietario() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [ativo, setAtivo] = useState<Ativo | null>(null)
  // Foto do PRÓPRIO barco na capa. Antes era uma imagem de banco fixa no
  // código: o armador abria o portal e via o barco de outra pessoa — logo no
  // momento em que ele deveria reconhecer o dele.
  const [capa, setCapa] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        // A lista já vem filtrada pelo backend: o armador só recebe os barcos
        // com o e-mail dele. Não há o que escolher aqui.
        const lista = await api.ativos.list()
        const arr = Array.isArray(lista) ? lista : []
        const meu = arr[0] || null
        setAtivo(meu)

        if (meu?.id) {
          try {
            const docs = await api.documentos.list(meu.id)
            const fotos = (Array.isArray(docs) ? docs : []).filter(
              (d: any) => d?.tipo === 'foto' && d?.url_arquivo,
            )
            // Vitrine primeiro: são as fotos de apresentação, escolhidas pela
            // marina justamente para mostrar o barco. Sem vitrine, qualquer
            // foto do cofre serve melhor que uma imagem genérica.
            const vitrine = fotos.find((d: any) => d.categoria === 'vitrine')
            setCapa((vitrine || fotos[0])?.url_arquivo || null)
          } catch {
            /* sem foto, a capa cai no fundo institucional */
          }
        }
      } catch {
        setAtivo(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#010c20] flex flex-col items-center justify-center">
        <div className="animate-spin w-12 h-12 border-2 border-[#c5a059] border-t-transparent rounded-full mb-6"></div>
        <span className="text-white/40 uppercase tracking-[0.3em] text-[10px] font-black">Acessando Cofre...</span>
      </div>
    )
  }

  if (!ativo) {
    return (
      <div className="min-h-screen bg-[#010c20] flex flex-col items-center justify-center px-6 text-center">
        <Anchor size={40} className="text-[#c5a059]/40 mb-6" />
        <h1 className="text-2xl font-serif font-bold text-white mb-2">Nenhuma embarcação vinculada</h1>
        <p className="text-white/40 text-sm max-w-md">
          Ainda não encontramos um ativo associado à sua conta. Fale com a marina responsável pelo seu cadastro.
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#010c20] to-[#021431] font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20] animate-in fade-in duration-1000">

      {/* Premium Header — responsivo (celular do proprietário até desktop) */}
      <div className="border-b border-white/10 bg-[#010c20]/90 backdrop-blur-xl sticky top-0 z-40">
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-5 flex items-center justify-between gap-3">
          {/* Logo (deslocada 15px para a esquerda no desktop) */}
          <img
            src="/logo-transparent.png"
            alt="Yachts Atlas"
            className="h-14 sm:h-20 md:h-[220px] w-auto object-contain flex-shrink-0 md:-ml-[27px]"
          />

          {/* Título — o TEXTO fica no centro exato do header; o escudo pende à esquerda sem deslocar o texto */}
          <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <div className="relative flex items-center justify-center">
              <Shield size={16} className="text-[#c5a059] hidden sm:block absolute right-full mr-3" />
              <span className="text-[9px] sm:text-[13px] md:text-[16px] font-black uppercase tracking-normal sm:tracking-[0.3em] text-white/40 whitespace-nowrap">
                Portal do Proprietário
              </span>
            </div>
          </div>

          <button
            onClick={() => navigate('/acesso-proprietario')}
            className="text-[12px] font-black uppercase tracking-widest text-white/30 hover:text-white transition-colors flex-shrink-0 whitespace-nowrap"
          >
            Sair do Cofre
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">

        {/* Welcome Section */}
        <div className="mb-16">
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-4">
            Seu Ativo. <span className="italic text-[#c5a059]">Seu Controle.</span>
          </h1>
          <p className="text-white/40 text-lg font-light max-w-2xl">
            Bem-vindo ao seu cofre digital restrito. Abaixo você tem o painel técnico exclusivo da sua embarcação — em modo visualização.
          </p>
        </div>

        {/* Vessel Banner */}
        <div className="relative rounded-sm overflow-hidden border border-white/10 aspect-[21/9] md:aspect-[21/6] mb-12 group">
          <img
            src={capa || '/boat-picture-light.jpg'}
            alt={ativo.nome_reg || `${ativo.marca} ${ativo.modelo}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-1000"
            onError={(e) => { e.currentTarget.src = '/boat-picture-light.jpg' }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-[#010c20]/50 to-transparent"></div>

          <div className="absolute bottom-8 left-8 right-8 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-[10px] font-black text-[#c5a059] border border-[#c5a059]/30 bg-[#c5a059]/10 px-3 py-1 rounded-sm uppercase tracking-widest">
                  {ativo.porte_categoria}
                </span>
                <span className="flex items-center gap-1.5 text-[10px] font-black text-emerald-400 uppercase tracking-widest">
                  <CheckCircle2 size={12} />
                  Ativo Certificado
                </span>
                {/* A nota que a marina vê, o dono também vê.
                    Ela é a prova de que a marina está alimentando o cofre —
                    mostrar ao armador reforça o trabalho dela, não expõe. */}
                {ativo.classificacao && (
                  <span
                    className={`text-[10px] font-black px-3 py-1 rounded-sm uppercase tracking-widest border ${
                      ativo.classificacao === 'gold'
                        ? 'text-[#c5a059] border-[#c5a059]/40 bg-[#c5a059]/10'
                        : ativo.classificacao === 'silver'
                        ? 'text-white/70 border-white/25 bg-white/5'
                        : 'text-amber-600/80 border-amber-600/30 bg-amber-600/10'
                    }`}
                    title="Índice de custódia: quanto do histórico deste ativo já está registrado e selado"
                  >
                    {ativo.classificacao === 'gold' ? 'Ouro'
                      : ativo.classificacao === 'silver' ? 'Prata' : 'Bronze'}
                    {typeof ativo.progresso === 'number' ? ` · ${ativo.progresso}%` : ''}
                  </span>
                )}
              </div>
              <h2 className="text-3xl font-serif font-bold text-white tracking-tight">{ativo.nome_reg || `${ativo.marca} ${ativo.modelo}`}</h2>
              <div className="flex items-center gap-4 mt-2 text-[10px] text-white/50 uppercase tracking-widest font-black">
                <span>{ativo.comprimento_pes} Pés</span>
                <span className="w-1 h-1 rounded-full bg-white/20"></span>
                <span>Ano {ativo.ano_fabricacao}</span>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-white/5 backdrop-blur-md border border-white/10 p-4 rounded-sm">
               <Anchor size={24} className="text-[#c5a059]" />
               <div>
                 <p className="text-[8px] uppercase tracking-widest text-white/40 font-black">Identificação Blockchain</p>
                 <p className="text-xs font-mono text-white/80 mt-1">{ativo.id}</p>
               </div>
            </div>
          </div>
        </div>

        {/* ITEM 1: Painel Técnico — mesmo padrão do sistema das marinas, 100% visualização */}
        <div className="space-y-6 mb-12">
          <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
            <Wrench size={20} className="text-[#c5a059]" />
            1. Painel Técnico
          </h3>
          <div className="bg-white/[0.02] border border-white/5 rounded-sm p-4 sm:p-8 shadow-2xl">
            <AtivoHub ativo={ativo} onBack={() => {}} readOnly hideHeader />
          </div>
        </div>

        {/* ITEM 2: Dossiê — aviso apenas, sem ação. Emissão/entrega é sempre pela marina. */}
        <div className="space-y-6 max-w-xl">
          <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
             <FileCheck size={20} className="text-[#c5a059]" />
             2. Dossiê Oficial
          </h3>

          <div className="bg-white/[0.02] border border-white/5 rounded-sm p-6 flex items-start gap-4">
            <div className="w-10 h-10 rounded-sm bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center flex-shrink-0">
              <FileCheck size={20} className="text-[#c5a059]" />
            </div>
            <div>
              <p className="text-sm font-medium text-white mb-1">Precisa do dossiê da sua embarcação?</p>
              <p className="text-[13px] text-white/50 leading-relaxed">
                O dossiê é emitido e entregue diretamente pela Marina Parceira Yachts Atlas responsável pelo seu ativo. Entre em contato com ela para solicitar.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
