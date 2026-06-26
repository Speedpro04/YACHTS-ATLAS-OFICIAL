import { useState, useEffect } from 'react'
import { Ativo } from '../types'
import { api } from '../services/api'
import {
  ArrowLeft, Ship, FileText, Wrench, Zap, Cpu, Shield, Paintbrush, Armchair,
  FileCheck, Camera, ShieldCheck, Sailboat, Plus, CalendarClock,
  Award, ChevronRight, X, Download, Upload, Lock
} from 'lucide-react'

type Health = 'ok' | 'warning' | 'critical' | 'info' | 'na'

interface Categoria {
  key: string
  titulo: string
  subtitulo: string
  icon: typeof Ship
  healthKey?: string
}

function categorias(tipo: Ativo['tipo']): Categoria[] {
  const base: Categoria[] = [
    { key: 'documentacao', titulo: 'Documentação', subtitulo: 'Legal & Conformidade', icon: FileText, healthKey: 'documentacao' },
    { key: 'seguro', titulo: 'Seguro', subtitulo: 'Apólice & Cobertura', icon: ShieldCheck },
    { key: 'manutencao', titulo: 'Manutenção', subtitulo: 'Serviços & Revisões', icon: Wrench, healthKey: 'manutencao' },
    { key: 'fotos', titulo: 'Fotos', subtitulo: 'Registro Visual', icon: Camera },
    { key: 'motor', titulo: 'Motor', subtitulo: 'Propulsão & Mecânica', icon: Zap, healthKey: 'motor' },
    { key: 'eletrica', titulo: 'Elétrica', subtitulo: 'Eletrônica & Navegação', icon: Cpu, healthKey: 'eletrica' },
    { key: 'seguranca', titulo: 'Segurança', subtitulo: 'Salvatagem & Proteção', icon: Shield, healthKey: 'seguranca' },
    { key: 'pintura', titulo: 'Pintura', subtitulo: 'Estética & Superfície', icon: Paintbrush, healthKey: 'pintura' },
    { key: 'interior', titulo: 'Interior', subtitulo: 'Acomodações & Conforto', icon: Armchair, healthKey: 'interior' },
    { key: 'dossie', titulo: 'Dossiê', subtitulo: 'Integridade Certificada', icon: FileCheck, healthKey: 'dossie' },
  ]
  if (tipo === 'veleiro') {
    return base.map((c) =>
      c.key === 'motor'
        ? { key: 'velame', titulo: 'Mastro & Velame', subtitulo: 'Rigging & Velas', icon: Sailboat, healthKey: 'motor' }
        : c
    )
  }
  if (tipo === 'jetski') {
    return base.filter((c) => !['interior', 'pintura'].includes(c.key))
  }
  return base
}

const HEALTH_STYLE: Record<Health, { dot: string; label: string; text: string }> = {
  ok: { dot: 'bg-emerald-400', label: 'Em dia', text: 'text-emerald-400' },
  warning: { dot: 'bg-amber-400', label: 'Atenção', text: 'text-amber-400' },
  critical: { dot: 'bg-rose-400', label: 'Crítico', text: 'text-rose-400' },
  info: { dot: 'bg-blue-400', label: 'Informativo', text: 'text-blue-400' },
  na: { dot: 'bg-white/20', label: 'Sem registro', text: 'text-white/30' },
}

const CLASSIF: Record<string, { label: string; cls: string }> = {
  gold: { label: 'Ouro', cls: 'bg-[#c5a059] text-[#010c20] border-[#c5a059]' },
  silver: { label: 'Prata', cls: 'bg-white/80 text-[#010c20] border-white' },
  bronze: { label: 'Bronze', cls: 'bg-[#a06a3c]/20 text-[#c98b54] border-[#a06a3c]/40' },
}

interface Props {
  ativo: Ativo
  onBack: () => void
}

export default function AtivoHub({ ativo, onBack }: Props) {
  const [secao, setSecao] = useState<Categoria | null>(null)
  const [contagem, setContagem] = useState<Record<string, number>>({})
  const cats = categorias(ativo.tipo)
  const classif = CLASSIF[ativo.classificacao] || CLASSIF.bronze

  // Contagem real de registros por categoria (dá vida aos cards)
  const carregarContagem = async () => {
    try {
      const data = await api.registros.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      const c: Record<string, number> = {}
      arr.forEach((r: any) => { c[r.categoria] = (c[r.categoria] || 0) + 1 })
      setContagem(c)
    } catch {
      setContagem({})
    }
  }

  useEffect(() => { carregarContagem() /* eslint-disable-next-line */ }, [ativo.id, secao])

  const statusDe = (c: Categoria): Health =>
    (c.healthKey ? (ativo.health_status?.[c.healthKey] as Health) : undefined) || 'na'

  return (
    <div className="animate-in fade-in slide-in-from-right-6 duration-500 space-y-8">
      {/* ===== BLOCO DE CIMA — Dados da embarcação ===== */}
      <div className="relative rounded-sm overflow-hidden border border-white/10">
        <div className="absolute inset-0">
          <img src="/boat-picture-light.jpg" alt="" className="w-full h-full object-cover opacity-25" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#010c20] via-[#010c20]/90 to-[#021a3d]/60" />
        </div>
        <div className="relative z-10 p-8">
          <button onClick={onBack} className="flex items-center gap-2 text-white/50 hover:text-[#c5a059] transition-all mb-6 text-[10px] font-black uppercase tracking-[0.2em]">
            <ArrowLeft size={14} /> Voltar à frota
          </button>
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 bg-[#010c20] border border-[#c5a059]/30 rounded-sm flex items-center justify-center text-[#c5a059] shadow-xl">
                <Ship size={34} strokeWidth={1} />
              </div>
              <div>
                <h1 className="text-3xl font-serif font-bold text-white tracking-tight">{ativo.marca} {ativo.modelo}</h1>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-white/40">
                  <span className="capitalize">{ativo.tipo.replace('_', ' ')}</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>{ativo.comprimento_pes || '—'} pés</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>{ativo.ano_fabricacao}</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>#{String(ativo.id).slice(0, 8).toUpperCase()}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border ${classif.cls}`}>
                <Award size={11} className="inline mr-1.5 -mt-0.5" />{classif.label}
              </span>
              <span className="px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border border-white/15 text-white/60 bg-white/5">
                Saúde {ativo.progresso || 0}%
              </span>
              <span className="flex items-center gap-2 px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border border-white/10 text-white/30" title="Registros são imutáveis — não podem ser editados">
                <Lock size={11} /> Imutável
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== BLOCO DE BAIXO — Painel Técnico (cards) ===== */}
      {!secao ? (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div>
            <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
              <Wrench size={20} className="text-[#c5a059]" /> Painel Técnico
            </h2>
            <p className="text-white/30 text-[10px] mt-1.5 uppercase tracking-[0.3em] font-black">
              Acesso às categorias da embarcação
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5">
            {cats.map((c) => {
              const n = contagem[c.key] || 0
              const st = statusDe(c)
              const hs = HEALTH_STYLE[st]
              const temRegistro = n > 0
              return (
                <button
                  key={c.key}
                  onClick={() => setSecao(c)}
                  className="group relative text-left bg-[#021431] border border-white/[0.06] rounded-sm p-7 transition-all duration-500 hover:border-[#c5a059]/40 hover:-translate-y-0.5 hover:bg-[#021a3d] shadow-xl overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-24 h-24 bg-[#c5a059]/0 group-hover:bg-[#c5a059]/5 blur-2xl rounded-full transition-all duration-700" />
                  <div className="relative z-10">
                    <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] mb-6 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                      <c.icon size={22} strokeWidth={1.5} />
                    </div>
                    <h3 className="text-white text-base font-serif font-bold tracking-tight group-hover:text-[#c5a059] transition-colors">{c.titulo}</h3>
                    <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] font-black mt-1">{c.subtitulo}</p>
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/5">
                      <span className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${temRegistro ? 'bg-[#c5a059]' : hs.dot}`} />
                        <span className={`text-[9px] font-black uppercase tracking-[0.15em] ${temRegistro ? 'text-[#c5a059]' : hs.text}`}>
                          {temRegistro ? `${n} ${n === 1 ? 'registro' : 'registros'}` : 'Sem registro'}
                        </span>
                      </span>
                      <ChevronRight size={15} className="text-white/15 group-hover:text-[#c5a059] group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ) : (secao.key === 'fotos' || secao.key === 'documentacao') ? (
        <UploadSecao categoria={secao} ativo={ativo} onBack={() => setSecao(null)} />
      ) : (
        <SecaoDetalhe categoria={secao} ativo={ativo} onBack={() => setSecao(null)} />
      )}
    </div>
  )
}

/* ===== Fotos / Documentação — UPLOAD real (Supabase Storage) ===== */
function UploadSecao({ categoria, ativo, onBack }: { categoria: Categoria; ativo: Ativo; onBack: () => void }) {
  const Icon = categoria.icon
  const isFotos = categoria.key === 'fotos'
  const [docs, setDocs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  const carregar = async () => {
    setLoading(true)
    try {
      const data = await api.documentos.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      setDocs(arr.filter((d: any) => d.categoria === categoria.key))
    } catch {
      setDocs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() /* eslint-disable-next-line */ }, [categoria.key, ativo.id])

  const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || !files.length) return
    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        const fd = new FormData()
        fd.append('file', file)
        await api.documentos.upload(ativo.id, isFotos ? 'foto' : 'documento', categoria.key, fd)
      }
      await carregar()
    } catch {
      alert('Falha no upload. O primeiro envio pode levar ~20s (servidor acordando). Tente novamente se preciso.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
          <ArrowLeft size={16} />
        </button>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <Icon size={20} className="text-[#c5a059]" /> {categoria.titulo}
          <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· {categoria.subtitulo}</span>
        </h2>
      </div>

      <label className={`block border border-dashed rounded-sm p-10 text-center cursor-pointer transition-all ${uploading ? 'border-[#c5a059]/40 bg-[#c5a059]/5 pointer-events-none' : 'border-white/10 hover:border-[#c5a059]/50 bg-white/[0.02]'}`}>
        <input type="file" className="hidden" multiple accept={isFotos ? 'image/png,image/jpeg' : '.pdf,.jpg,.jpeg,.png'} disabled={uploading} onChange={handleFiles} />
        {uploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4" />
            <span className="text-[10px] font-black text-[#c5a059] uppercase tracking-widest">Enviando e selando (SHA-256)...</span>
          </div>
        ) : (
          <>
            <Upload size={32} className="mx-auto text-white/15 mb-4" />
            <p className="text-white text-xs font-black uppercase tracking-widest mb-1">{isFotos ? 'Adicionar Fotos' : 'Enviar Documento'}</p>
            <p className="text-white/25 text-[10px] uppercase tracking-widest">{isFotos ? 'PNG, JPG até 10MB' : 'PDF, PNG, JPG até 10MB'} · pode selecionar várias</p>
          </>
        )}
      </label>

      {loading ? (
        <div className="flex items-center justify-center py-12"><div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full" /></div>
      ) : docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12 bg-white/[0.01] border border-dashed border-white/10 rounded-sm">
          <Icon size={40} strokeWidth={1} className="text-white/10 mb-4" />
          <p className="text-white/50 text-sm font-bold uppercase tracking-[0.2em]">{isFotos ? 'Sem fotos ainda' : 'Cofre vazio'}</p>
        </div>
      ) : isFotos ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {docs.map((d) => (
            <div key={d.id} className="group relative rounded-sm overflow-hidden border border-white/10 aspect-square bg-[#021431]">
              <img src={d.url_arquivo} alt={d.nome_arquivo} className="w-full h-full object-cover" loading="lazy" />
              <a href={d.url_arquivo} target="_blank" rel="noopener noreferrer" download className="absolute inset-0 flex items-center justify-center bg-[#010c20]/0 group-hover:bg-[#010c20]/70 opacity-0 group-hover:opacity-100 transition-all">
                <span className="flex items-center gap-2 text-[#c5a059] text-[10px] font-black uppercase tracking-widest"><Download size={16} /> Baixar</span>
              </a>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {docs.map((d) => (
            <div key={d.id} className="bg-[#021431] border border-white/5 rounded-sm p-4 flex items-center justify-between gap-4 hover:border-[#c5a059]/20 transition-all">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 flex-shrink-0 bg-[#050b18] border border-white/5 rounded-sm flex items-center justify-center text-[#c5a059]"><FileText size={18} /></div>
                <div className="min-w-0">
                  <p className="text-white text-sm font-bold truncate">{d.nome_arquivo}</p>
                  <p className="text-white/30 text-[9px] uppercase tracking-widest mt-0.5">{((d.tamanho_bytes || 0) / 1024).toFixed(0)} KB · {d.created_at ? new Date(d.created_at).toLocaleDateString('pt-BR') : ''}</p>
                </div>
              </div>
              <a href={d.url_arquivo} target="_blank" rel="noopener noreferrer" download className="flex-shrink-0 text-white/30 hover:text-[#c5a059] p-2 transition-all"><Download size={18} /></a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ===== Painel de uma categoria — FUNCIONAL (lista + cria registro real) ===== */
const STATUS_OPCOES = [
  { v: 'registrado', label: 'Registrado' },
  { v: 'concluido', label: 'Concluído' },
  { v: 'pendente', label: 'Pendente' },
  { v: 'atencao', label: 'Atenção' },
]
const STATUS_COR: Record<string, string> = {
  registrado: 'text-[#c5a059] border-[#c5a059]/30 bg-[#c5a059]/10',
  concluido: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  pendente: 'text-amber-400 border-amber-400/30 bg-amber-400/10',
  atencao: 'text-rose-400 border-rose-400/30 bg-rose-400/10',
}

function SecaoDetalhe({ categoria, ativo, onBack }: { categoria: Categoria; ativo: Ativo; onBack: () => void }) {
  const Icon = categoria.icon
  const isManut = categoria.key === 'manutencao'
  const [registros, setRegistros] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const agora = new Date()
  const hojeLocal = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
  const formVazio = { titulo: '', responsavel: '', data: hojeLocal, hora: agora.toTimeString().slice(0, 5), local: '', custo: '', observacao: '', status: 'registrado' }
  const [form, setForm] = useState(formVazio)

  const carregar = async () => {
    setLoading(true)
    try {
      const data = await api.registros.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      setRegistros(arr.filter((r: any) => r.categoria === categoria.key))
    } catch {
      setRegistros([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() /* eslint-disable-next-line */ }, [categoria.key, ativo.id])

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.titulo.trim()) return
    setSaving(true)
    try {
      const dados: Record<string, string> = {}
      if (form.responsavel.trim()) dados.responsavel = form.responsavel.trim()
      if (form.data) dados.data_servico = form.data
      if (form.hora) dados.hora = form.hora
      if (form.local.trim()) dados.local = form.local.trim()
      if (form.custo.trim()) dados.custo = form.custo.trim()
      await api.registros.create({
        ativo_id: ativo.id,
        categoria: categoria.key,
        titulo: form.titulo.trim(),
        observacao: form.observacao.trim() || undefined,
        dados,
        status: form.status as any,
      })
      setForm(formVazio)
      setShowForm(false)
      await carregar()
    } catch {
      alert('Não foi possível salvar o registro. Verifique a conexão com o servidor.')
    } finally {
      setSaving(false)
    }
  }

  const inputCls = 'w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20'

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
            <ArrowLeft size={16} />
          </button>
          <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
            <Icon size={20} className="text-[#c5a059]" /> {categoria.titulo}
            <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· {categoria.subtitulo}</span>
          </h2>
        </div>
        <button onClick={() => setShowForm((s) => !s)} className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-6 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all">
          {showForm ? <X size={15} /> : <Plus size={15} />}
          {showForm ? 'Fechar' : isManut ? 'Nova Ordem de Serviço' : 'Adicionar Registro'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={salvar} className="bg-[#021431] border border-white/10 rounded-sm p-6 space-y-4 animate-in slide-in-from-top-2 duration-300">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">{isManut ? 'Serviço executado' : 'Título'}</label>
              <input className={inputCls} value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} placeholder={isManut ? 'Ex: Revisão dos motores' : 'Ex: Renovação do seguro'} required />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Quem fez / responsável</label>
              <input className={inputCls} value={form.responsavel} onChange={(e) => setForm({ ...form, responsavel: e.target.value })} placeholder="Técnico, empresa, marina..." />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Data do serviço</label>
              <input type="date" className={inputCls} value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Hora</label>
              <input type="time" className={inputCls} value={form.hora} onChange={(e) => setForm({ ...form, hora: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Local / Oficina</label>
              <input className={inputCls} value={form.local} onChange={(e) => setForm({ ...form, local: e.target.value })} placeholder="Opcional" />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Custo (R$)</label>
              <input className={inputCls} value={form.custo} onChange={(e) => setForm({ ...form, custo: e.target.value })} placeholder="Opcional" />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Observação</label>
            <textarea className={inputCls + ' resize-none'} rows={2} value={form.observacao} onChange={(e) => setForm({ ...form, observacao: e.target.value })} placeholder="Detalhes do registro..." />
          </div>
          <div className="flex items-end justify-between gap-4 flex-wrap">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Status</label>
              <select className={inputCls + ' min-w-[160px]'} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                {STATUS_OPCOES.map((s) => <option key={s.v} value={s.v} className="bg-[#010c20]">{s.label}</option>)}
              </select>
            </div>
            <button type="submit" disabled={saving} className="bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] px-8 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all">
              {saving ? 'Salvando...' : 'Salvar Registro'}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full" />
        </div>
      ) : registros.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-16 bg-white/[0.01] border border-dashed border-white/10 rounded-sm">
          <Icon size={40} strokeWidth={1} className="text-white/10 mb-4" />
          <p className="text-white/50 text-sm font-bold uppercase tracking-[0.2em]">Nada registrado ainda</p>
          <p className="text-white/25 text-xs mt-2">Clique em "{isManut ? 'Nova Ordem de Serviço' : 'Adicionar Registro'}" para criar o primeiro.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {registros.map((r) => (
            <div key={r.id} className="bg-[#021431] border border-white/5 rounded-sm p-5 hover:border-[#c5a059]/20 transition-all">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-white font-bold text-sm">{r.titulo || '(sem título)'}</p>
                  {(r.dados?.responsavel || r.dados?.data_servico || r.dados?.local || r.dados?.custo) && (
                    <p className="text-white/45 text-[11px] mt-1">
                      {r.dados?.responsavel ? `Por ${r.dados.responsavel}` : ''}
                      {r.dados?.data_servico ? ` · ${String(r.dados.data_servico).split('-').reverse().join('/')}` : ''}
                      {r.dados?.hora ? ` às ${r.dados.hora}` : ''}
                      {r.dados?.local ? ` · ${r.dados.local}` : ''}
                      {r.dados?.custo ? ` · R$ ${r.dados.custo}` : ''}
                    </p>
                  )}
                  {r.observacao && <p className="text-white/40 text-xs mt-2 leading-relaxed">{r.observacao}</p>}
                </div>
                <span className={`flex-shrink-0 px-3 py-1 rounded-sm text-[8px] font-black uppercase tracking-[0.15em] border ${STATUS_COR[r.status] || STATUS_COR.registrado}`}>
                  {r.status}
                </span>
              </div>
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-2 text-white/25 text-[9px] font-black uppercase tracking-[0.2em]">
                <CalendarClock size={12} />
                {r.created_at ? new Date(r.created_at).toLocaleString('pt-BR') : ''}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
