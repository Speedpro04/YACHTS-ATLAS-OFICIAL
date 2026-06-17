import { useEffect, useState, useCallback } from 'react'
import { FileCheck, Mail, Phone, Ship, Check, X, RefreshCw, ShieldCheck, Clock } from 'lucide-react'
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
  const [itens, setItens] = useState<Solicitacao[]>([])
  const [filtro, setFiltro] = useState<string>('')
  const [carregando, setCarregando] = useState(true)
  const [acaoId, setAcaoId] = useState<string>('')
  const [erro, setErro] = useState('')

  const carregar = useCallback(async () => {
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

  useEffect(() => { carregar() }, [carregar])

  const liberar = async (id: string) => {
    setAcaoId(id)
    try {
      await api.dossie.liberar(id)
      await carregar()
    } catch {
      setErro('Falha ao liberar. Tente novamente.')
    } finally {
      setAcaoId('')
    }
  }

  const recusar = async (id: string) => {
    setAcaoId(id)
    try {
      await api.dossie.recusar(id)
      await carregar()
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

  const pendentes = itens.filter((i) => i.status === 'pendente').length

  return (
    <div className="max-w-6xl mx-auto">
      {/* Cabeçalho */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
        <div>
          <div className="inline-flex items-center gap-2 mb-3">
            <FileCheck size={18} className="text-[#c5a059]" />
            <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">Dossiês</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-tight">Pedidos de Dossiê</h1>
          <p className="text-white/40 text-sm mt-2">
            {pendentes > 0 ? `${pendentes} pedido(s) aguardando liberação` : 'Nenhum pedido pendente'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
            className="bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-xs uppercase tracking-widest outline-none focus:border-[#c5a059] appearance-none"
          >
            <option value="" className="bg-[#010c20]">Todos</option>
            <option value="pendente" className="bg-[#010c20]">Pendentes</option>
            <option value="liberado" className="bg-[#010c20]">Liberados</option>
            <option value="recusado" className="bg-[#010c20]">Recusados</option>
          </select>
          <button
            onClick={carregar}
            className="p-3 border border-white/10 rounded-sm text-white/50 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all"
            title="Atualizar"
          >
            <RefreshCw size={16} className={carregando ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {erro && <p className="text-rose-400 text-sm mb-6">{erro}</p>}

      {carregando && itens.length === 0 ? (
        <div className="text-center py-24 text-white/30 text-sm uppercase tracking-widest">Carregando…</div>
      ) : itens.length === 0 ? (
        <div className="text-center py-24 border border-white/5 rounded-sm bg-white/[0.01]">
          <FileCheck size={40} className="text-white/10 mx-auto mb-4" />
          <p className="text-white/40 text-sm">Nenhum pedido por aqui ainda.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {itens.map((s) => (
            <div key={s.id} className="bg-[#021431] border border-white/5 rounded-sm p-6 hover:border-white/10 transition-all">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
                {/* Dados do solicitante */}
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

                {/* Ações */}
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
  )
}
