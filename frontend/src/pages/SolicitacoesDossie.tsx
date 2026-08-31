import { useEffect, useState, useCallback } from 'react'
import { FileCheck, Mail, Phone, Ship, Check, X, RefreshCw, ShieldCheck, Clock, Download, Lock, Search } from 'lucide-react'
import { api } from '../services/api'

interface Solicitacao {
  id: string
  ativo_id?: string
  marina_nome?: string
  solicitante_nome: string
  solicitante_email: string
  solicitante_telefone?: string
  finalidade: string
  mensagem?: string
  status: 'pendente' | 'liberado' | 'recusado'
  acessos?: number
  ultimo_acesso?: string
  created_at: string
}

const FINALIDADE_LABEL: Record<string, string> = {
  venda: 'Compra / Venda',
  seguro: 'Seguro',
  outro: 'Outro',
}

const STATUS_STYLE: Record<string, string> = {
  pendente: 'text-amber-400 border-amber-400/30 bg-amber-400/5',
  liberado: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/5',
  recusado: 'text-rose-400 border-rose-400/30 bg-rose-400/5',
}

export default function SolicitacoesDossie() {
  const [activeTab, setActiveTab] = useState<'gerar' | 'pedidos'>('gerar')
  
  // Tab 1: Gerar Dossiê
  const [ativos, setAtivos] = useState<any[]>([])
  const [searchAtivo, setSearchAtivo] = useState('')
  const [loadingAtivos, setLoadingAtivos] = useState(false)
  const [generatingAtivoId, setGeneratingAtivoId] = useState<string | null>(null)

  // Tab 2: Pedidos de Acesso
  const [itens, setItens] = useState<Solicitacao[]>([])
  const [filtro, setFiltro] = useState<string>('')
  const [carregando, setCarregando] = useState(true)
  const [acaoId, setAcaoId] = useState<string>('')
  const [erro, setErro] = useState('')

  const carregarPedidos = useCallback(async () => {
    setCarregando(true)
    setErro('')
    try {
      const data = await api.dossie.listSolicitacoes(filtro || undefined)
      setItens(Array.isArray(data) ? data : [])
    } catch {
      setErro('Não foi possível carregar os pedidos.')
    } finally {
      setCarregando(false)
    }
  }, [filtro])

  const carregarAtivos = async () => {
    setLoadingAtivos(true)
    try {
      const data = await api.ativos.list()
      const lista = Array.isArray(data) ? data : []
      setAtivos(lista)
      // Saldo de cada um, em paralelo. Sem isto os cards nasceriam sem número
      // e voltariam a depender de um palpite local.
      lista.forEach((a: any) => carregarSaldo(a.id))
    } catch {
      console.error('Falha ao carregar ativos')
    } finally {
      setLoadingAtivos(false)
    }
  }

  useEffect(() => {
    carregarAtivos()
  }, [])

  useEffect(() => {
    if (activeTab === 'pedidos') {
      carregarPedidos()
    }
  }, [activeTab, carregarPedidos])

  const liberar = async (id: string) => {
    setAcaoId(id)
    try {
      await api.dossie.liberar(id)
      await carregarPedidos()
    } catch (e: any) {
      // A mensagem do servidor vem inteira, de propósito. O `catch` vazio
      // que existia aqui trocava TODA recusa por "Tente novamente" — e as
      // duas recusas reais que esta rota dá são justamente as que repetir
      // não resolve: cota anual esgotada (429) e consentimento do titular
      // ausente ou retirado (409). A marina clicava de novo, via o mesmo
      // texto, e ligava para o suporte perguntar o que estava acontecendo.
      setErro(e?.message || 'Falha ao liberar. Tente novamente.')
    } finally {
      setAcaoId('')
    }
  }

  const recusar = async (id: string) => {
    setAcaoId(id)
    try {
      await api.dossie.recusar(id)
      await carregarPedidos()
    } catch {
      setErro('Falha ao recusar. Tente novamente.')
    } finally {
      setAcaoId('')
    }
  }

  const fmtData = (iso?: string) => {
    if (!iso) return '—'
    try { return new Date(iso).toLocaleString('pt-BR') } catch { return iso }
  }

  // Saldo por ativo, vindo do SERVIDOR.
  //
  // Esta tela tinha a MESMA regra do `AtivoHub`, escrita de novo e lendo o
  // `localStorage`. Em 26/08/2026 a tela de detalhe foi corrigida e esta
  // continuou mostrando "4/4 restantes" logo depois de emitir — a mesma regra
  // em dois lugares, um consertado e o outro não. É o padrão que já custou a
  // senha (6/8/10), o preço, o telefone e as categorias.
  //
  // Agora as duas leem `GET /dossie/{id}/saldo`, e não existe cópia da conta.
  type Saldo = { allowed: boolean; remaining: number; limite: number; resetDate?: Date }
  const [saldos, setSaldos] = useState<Record<string, Saldo>>({})

  const carregarSaldo = async (ativoId: string) => {
    try {
      const s = await api.dossie.saldo(ativoId)
      setSaldos((prev) => ({
        ...prev,
        [ativoId]: {
          allowed: !!s.permitido,
          remaining: s.restantes ?? 0,
          // O teto também vem do servidor: está em variável de ambiente, e
          // number escrito na tela envelhece calado quando a regra muda.
          limite: s.limite ?? 0,
          resetDate: s.reset_em ? new Date(s.reset_em) : undefined,
        },
      }))
    } catch {
      // Sem saldo conhecido o botão segue habilitado: quem recusa de verdade é
      // o servidor, no momento da emissão.
      setSaldos((prev) => ({ ...prev, [ativoId]: { allowed: true, remaining: 0, limite: 0 } }))
    }
  }

  const checkLimit = (ativoId: string): Saldo =>
    saldos[ativoId] ?? { allowed: true, remaining: 0, limite: 0 }

  const handleGerarDossie = async (ativo: any) => {
    const lim = checkLimit(ativo.id)
    if (!lim.allowed) {
      alert(`Limite anual de dossiês atingido para esta embarcação. Próxima emissão disponível em: ${lim.resetDate?.toLocaleDateString('pt-BR')}`)
      return
    }
    setGeneratingAtivoId(ativo.id)
    try {
      const url = await api.dossie.pdfUrl(ativo.id)
      await carregarSaldo(ativo.id)
      const a = document.createElement('a')
      a.href = url
      a.download = `dossie_${ativo.marca.toLowerCase()}_${ativo.modelo.toLowerCase()}_${ativo.id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      // trigger rerender to update balance display
      setAtivos(prev => [...prev])
    } catch (err: any) {
      alert('Erro ao gerar dossiê: ' + (err?.message || err))
    } finally {
      setGeneratingAtivoId(null)
    }
  }

  const ativosFiltrados = ativos.filter((a) => {
    const term = searchAtivo.toLowerCase()
    return (
      a.marca?.toLowerCase().includes(term) ||
      a.modelo?.toLowerCase().includes(term) ||
      a.id?.toLowerCase().includes(term)
    )
  })

  const pendentes = itens.filter((i) => i.status === 'pendente').length

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Cabeçalho */}
      <div>
        <div className="inline-flex items-center gap-2 mb-3">
          <FileCheck size={18} className="text-[#c5a059]" />
          <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">Serviços Náuticos</span>
        </div>
        <h1 className="text-3xl font-serif font-bold text-white tracking-tight">Custódia & Conformidade</h1>
        <p className="text-white/40 text-sm mt-2">
          Gerencie e emita dossiês oficiais de conformidade técnica para as embarcações sob custódia da marina.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5">
        <button
          onClick={() => setActiveTab('gerar')}
          className={`px-6 py-3.5 text-xs font-black uppercase tracking-widest border-b-2 transition-all ${
            activeTab === 'gerar'
              ? 'border-[#c5a059] text-[#c5a059]'
              : 'border-transparent text-white/40 hover:text-white'
          }`}
        >
          Gerar Dossiê
        </button>
        <button
          onClick={() => setActiveTab('pedidos')}
          className={`px-6 py-3.5 text-xs font-black uppercase tracking-widest border-b-2 transition-all flex items-center gap-2 ${
            activeTab === 'pedidos'
              ? 'border-[#c5a059] text-[#c5a059]'
              : 'border-transparent text-white/40 hover:text-white'
          }`}
        >
          Pedidos de Acesso
          {pendentes > 0 && (
            <span className="bg-amber-500 text-[#010c20] text-[9px] font-black px-1.5 py-0.5 rounded-full">
              {pendentes}
            </span>
          )}
        </button>
      </div>

      {/* Conteúdo Aba 1: Gerar Dossiê */}
      {activeTab === 'gerar' && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Barra de Pesquisa */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
            <input
              type="text"
              value={searchAtivo}
              onChange={(e) => setSearchAtivo(e.target.value)}
              placeholder="Pesquise por marca, modelo ou ID da embarcação..."
              className="w-full bg-[#021431] border border-white/10 rounded-sm pl-12 pr-4 py-4 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20"
            />
          </div>

          {loadingAtivos ? (
            <div className="text-center py-24 text-white/30 text-sm uppercase tracking-widest">Carregando frota…</div>
          ) : ativosFiltrados.length === 0 ? (
            <div className="text-center py-24 border border-white/5 rounded-sm bg-white/[0.01]">
              <Ship size={40} className="text-white/10 mx-auto mb-4" />
              <p className="text-white/40 text-sm">Nenhuma embarcação encontrada para a pesquisa.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ativosFiltrados.map((a) => {
                const lim = checkLimit(a.id)
                const isGenerating = generatingAtivoId === a.id
                return (
                  <div key={a.id} className="bg-[#021431] border border-white/5 rounded-sm p-6 hover:border-[#c5a059]/20 transition-all flex flex-col justify-between gap-5">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] shrink-0">
                        <Ship size={24} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-white font-serif font-bold text-lg truncate">{a.nome_reg || `${a.marca} ${a.modelo}`}</h3>
                        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-[9px] font-black uppercase tracking-widest text-white/40">
                          <span>{a.tipo}</span>
                          <span>•</span>
                          <span>{a.comprimento_pes} pés</span>
                          <span>•</span>
                          <span>{a.ano_fabricacao}</span>
                        </div>
                        <p className="text-[9px] font-mono text-white/35 mt-1">ID: {a.id.toUpperCase()}</p>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-white/5">
                      <div className="text-left">
                        <p className="text-[9px] font-black uppercase tracking-wider text-white/30">Saldo de Dossiês</p>
                        <p className={`text-sm font-bold ${lim.remaining > 0 ? 'text-[#c5a059]' : 'text-rose-400'}`}>
                          {lim.remaining} / {lim.limite} restantes
                        </p>
                        {!lim.allowed && lim.resetDate && (
                          <p className="text-[8px] text-[#c5a059] uppercase tracking-widest font-black mt-1">
                            Disponível em: {lim.resetDate.toLocaleDateString('pt-BR')}
                          </p>
                        )}
                      </div>

                      {lim.allowed ? (
                        <button
                          onClick={() => handleGerarDossie(a)}
                          disabled={isGenerating}
                          className="flex items-center justify-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] px-5 py-3 rounded-sm text-[10px] font-black uppercase tracking-widest transition-all shrink-0"
                        >
                          {isGenerating ? (
                            <div className="animate-spin w-3.5 h-3.5 border-2 border-[#010c20] border-t-transparent rounded-full" />
                          ) : (
                            <Download size={14} />
                          )}
                          Gerar Dossiê
                        </button>
                      ) : (
                        <div className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-[#c5a059] bg-[#c5a059]/10 border border-[#c5a059]/20 px-4 py-2.5 rounded-sm">
                          <Lock size={12} /> Limite Atingido
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Conteúdo Aba 2: Pedidos de Acesso */}
      {activeTab === 'pedidos' && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-white font-serif font-bold text-lg">Pedidos de Acesso Externos</h2>
            <div className="flex items-center gap-3">
              <select
                value={filtro}
                onChange={(e) => setFiltro(e.target.value)}
                className="bg-[#021431] border border-white/10 rounded-sm px-4 py-3 text-white text-xs uppercase tracking-widest outline-none focus:border-[#c5a059] appearance-none"
              >
                <option value="" className="bg-[#010c20]">Todos</option>
                <option value="pendente" className="bg-[#010c20]">Pendentes</option>
                <option value="liberado" className="bg-[#010c20]">Liberados</option>
                <option value="recusado" className="bg-[#010c20]">Recusados</option>
              </select>
              <button
                onClick={carregarPedidos}
                className="p-3 border border-white/10 rounded-sm text-white/50 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all bg-[#021431]"
                title="Atualizar"
              >
                <RefreshCw size={16} className={carregando ? 'animate-spin' : ''} />
              </button>
            </div>
          </div>

          {erro && <p className="text-rose-400 text-sm">{erro}</p>}

          {carregando && itens.length === 0 ? (
            <div className="text-center py-24 text-white/30 text-sm uppercase tracking-widest">Carregando pedidos…</div>
          ) : itens.length === 0 ? (
            <div className="text-center py-24 border border-white/5 rounded-sm bg-white/[0.01]">
              <FileCheck size={40} className="text-white/10 mx-auto mb-4" />
              <p className="text-white/40 text-sm">Nenhum pedido pendente ou liberado.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {itens.map((s) => (
                <div key={s.id} className="bg-[#021431] border border-white/5 rounded-sm p-6 hover:border-white/10 transition-all">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span className="text-white font-bold text-base truncate">{s.solicitante_nome}</span>
                        <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded border ${STATUS_STYLE[s.status]}`}>
                          {s.status}
                        </span>
                        <span className="text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded border border-white/10 text-white/40">
                          {FINALIDADE_LABEL[s.finalidade] || s.finalidade}
                        </span>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-1.5 text-xs text-white/50">
                        <span className="flex items-center gap-2 truncate"><Mail size={12} className="text-white/30 flex-shrink-0" />{s.solicitante_email}</span>
                        {s.solicitante_telefone && <span className="flex items-center gap-2"><Phone size={12} className="text-white/30 flex-shrink-0" />{s.solicitante_telefone}</span>}
                        {s.ativo_id && <span className="flex items-center gap-2 truncate"><Ship size={12} className="text-white/30 flex-shrink-0" />{s.ativo_id}</span>}
                        {s.marina_nome && <span className="flex items-center gap-2 truncate"><ShieldCheck size={12} className="text-white/30 flex-shrink-0" />{s.marina_nome}</span>}
                      </div>
                      {s.mensagem && <p className="text-white/40 text-xs mt-3 italic">"{s.mensagem}"</p>}
                      <div className="flex items-center gap-4 mt-3 text-[10px] text-white/25 uppercase tracking-widest">
                        <span className="flex items-center gap-1.5"><Clock size={10} />{fmtData(s.created_at)}</span>
                        {s.status === 'liberado' && (
                          <span className="text-emerald-400/60">{s.acessos || 0} acesso(s) • último: {fmtData(s.ultimo_acesso)}</span>
                        )}
                      </div>
                    </div>

                    {s.status === 'pendente' && (
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <button
                          onClick={() => liberar(s.id)}
                          disabled={acaoId === s.id}
                          className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] px-5 py-3 rounded-sm text-[10px] font-black uppercase tracking-widest transition-all"
                        >
                          <Check size={14} /> Liberar
                        </button>
                        <button
                          onClick={() => recusar(s.id)}
                          disabled={acaoId === s.id}
                          className="flex items-center gap-2 border border-white/10 hover:border-rose-400/40 hover:text-rose-400 disabled:opacity-50 text-white/50 px-4 py-3 rounded-sm text-[10px] font-black uppercase tracking-widest transition-all"
                        >
                          <X size={14} /> Recusar
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
