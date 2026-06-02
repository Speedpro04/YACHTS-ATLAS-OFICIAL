import { useState, useRef } from 'react'
import {
  X, Save, Loader2, Camera, Check, AlertCircle,
  Anchor, Users, FileText, Ship, Gauge, Cpu, Wrench, ClipboardCheck,
  Waves, AlertTriangle, Sailboat, Armchair, TrendingUp, ShieldCheck, Globe, Lock,
} from 'lucide-react'
import { supabase, api } from '../services/api'
import type { Categoria, CategoriaField } from '../config/dossieCategorias'

// Mapa nome (config) -> ícone lucide
const ICONES: Record<string, React.ElementType> = {
  Anchor, Users, FileText, Ship, Gauge, Cpu, Wrench, ClipboardCheck,
  Waves, AlertTriangle, Camera, Sailboat, Armchair, TrendingUp, ShieldCheck, Globe, Lock,
}

interface CategoriaFormProps {
  categoria: Categoria
  ativoId: string
  ativoNome: string
  onClose: () => void
  onSaved?: () => void
}

export default function CategoriaForm({ categoria, ativoId, ativoNome, onClose, onSaved }: CategoriaFormProps) {
  const Icon = ICONES[categoria.icon] || FileText
  const [campos, setCampos] = useState<Record<string, string>>({})
  const [marcados, setMarcados] = useState<string[]>([])
  const [observacao, setObservacao] = useState('')
  const [arquivos, setArquivos] = useState<{ nome: string; url: string; hash: string; tamanho: number }[]>([])
  const [enviando, setEnviando] = useState(false)
  const [subindo, setSubindo] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const setCampo = (key: string, value: string) =>
    setCampos((prev) => ({ ...prev, [key]: value }))

  const toggleItem = (item: string) =>
    setMarcados((prev) => (prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]))

  // Calcula o SHA-256 do arquivo (custódia: sela o conteúdo no momento do upload)
  const sha256Hex = async (file: File): Promise<string> => {
    const buf = await file.arrayBuffer()
    const digest = await crypto.subtle.digest('SHA-256', buf)
    return Array.from(new Uint8Array(digest))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSubindo(true)
    try {
      const hash = await sha256Hex(file)
      const ext = file.name.split('.').pop()
      const path = `${ativoId}/${categoria.id}/${Date.now()}.${ext}`
      const { error } = await supabase.storage.from('media').upload(path, file, { upsert: false })
      if (error) throw error
      const { data } = supabase.storage.from('media').getPublicUrl(path)
      if (data?.publicUrl) {
        setArquivos((prev) => [...prev, { nome: file.name, url: data.publicUrl, hash, tamanho: file.size }])
      }
    } catch (err: any) {
      alert('Erro no upload: ' + (err?.message || err))
    } finally {
      setSubindo(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleSalvar = async () => {
    setEnviando(true)
    try {
      const titulo =
        (campos.nome || campos.titulo || campos.servico || campos.evento || categoria.label).toString().slice(0, 120)
      await api.registros.create({
        ativo_id: ativoId,
        categoria: categoria.id,
        titulo,
        observacao,
        dados: { ...campos, arquivos },
        checklist: marcados,
      })
      onSaved?.()
      onClose()
    } catch (err: any) {
      alert('Erro ao salvar: ' + (err?.message || err))
    } finally {
      setEnviando(false)
    }
  }

  const renderCampo = (f: CategoriaField) => {
    const base =
      'w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm outline-none transition-all focus:border-[#c5a059] placeholder:text-white/15'
    if (f.type === 'select') {
      return (
        <select className={`${base} appearance-none`} value={campos[f.key] || ''} onChange={(e) => setCampo(f.key, e.target.value)}>
          <option value="" className="bg-[#010c20]">Selecione</option>
          {f.options?.map((o) => (
            <option key={o} value={o} className="bg-[#010c20]">{o}</option>
          ))}
        </select>
      )
    }
    if (f.type === 'textarea') {
      return (
        <textarea
          className={`${base} min-h-[90px] resize-none`}
          placeholder={f.placeholder}
          value={campos[f.key] || ''}
          onChange={(e) => setCampo(f.key, e.target.value)}
        />
      )
    }
    return (
      <input
        type={f.type}
        className={base}
        placeholder={f.placeholder}
        value={campos[f.key] || ''}
        onChange={(e) => setCampo(f.key, e.target.value)}
      />
    )
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10">
      <div className="absolute inset-0 bg-[#010c20]/95 backdrop-blur-md animate-in fade-in duration-300" onClick={onClose} />

      <div className="relative w-full max-w-3xl bg-[#021431] border border-[#c5a059]/20 rounded-sm shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">
        {/* Cabeçalho — identidade da categoria */}
        <div className="p-8 border-b border-white/5 flex items-center justify-between shrink-0 bg-[#010c20]/80">
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 bg-[#c5a059]/10 border border-[#c5a059]/30 rounded-sm flex items-center justify-center text-[#c5a059]">
              <Icon size={26} strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="text-2xl font-serif font-bold text-white tracking-tight">{categoria.label}</h3>
              <p className="text-[10px] text-[#c5a059] uppercase tracking-[0.3em] mt-1.5 font-black">
                {categoria.dossieSecao} <span className="text-white/20 mx-2">•</span> {ativoNome}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="w-11 h-11 rounded-sm border border-white/5 flex items-center justify-center text-white/30 hover:text-[#c5a059] hover:border-[#c5a059]/30 transition-all">
            <X size={22} />
          </button>
        </div>

        {/* Conteúdo */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          <p className="text-white/40 text-sm font-light leading-relaxed">{categoria.descricao}</p>

          {/* Campos estruturados da categoria */}
          {categoria.campos && categoria.campos.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {categoria.campos.map((f) => (
                <div key={f.key} className={f.type === 'textarea' ? 'md:col-span-2' : ''}>
                  <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-white/40 mb-2">
                    {f.label}
                    {f.paisEspecifico && <span className="text-[#c5a059]/60 ml-2 normal-case tracking-normal">(por país)</span>}
                  </label>
                  {renderCampo(f)}
                </div>
              ))}
            </div>
          )}

          {/* Checklist da categoria */}
          {categoria.checklist && categoria.checklist.length > 0 && (
            <div className="pt-2">
              <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#c5a059] mb-4">Itens</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {categoria.checklist.map((item) => {
                  const on = marcados.includes(item)
                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => toggleItem(item)}
                      className={`flex items-center gap-3 p-3 rounded-sm border text-left transition-all ${
                        on ? 'bg-[#c5a059]/10 border-[#c5a059]/40' : 'bg-white/[0.02] border-white/5 hover:border-white/15'
                      }`}
                    >
                      <span className={`w-5 h-5 rounded-sm flex items-center justify-center border ${on ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 'border-white/20 text-transparent'}`}>
                        <Check size={13} strokeWidth={3} />
                      </span>
                      <span className={`text-[11px] ${on ? 'text-[#c5a059]' : 'text-white/50'}`}>{item}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Uploads com custódia */}
          {categoria.uploads && (
            <div className="pt-2">
              <div onClick={() => fileRef.current?.click()} className="p-8 border border-dashed border-white/10 rounded-sm flex flex-col items-center gap-3 hover:border-[#c5a059]/40 transition-all cursor-pointer bg-white/[0.01]">
                <div className="w-12 h-12 rounded-full bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059]">
                  {subindo ? <Loader2 size={20} className="animate-spin" /> : <Camera size={20} />}
                </div>
                <p className="text-sm text-[#e5d5b7] font-serif">{subindo ? 'Enviando...' : 'Anexar documento, laudo ou imagem'}</p>
                <p className="text-[9px] text-white/30 uppercase tracking-widest">
                  {arquivos.length > 0 ? <span className="text-[#c5a059] font-bold">{arquivos.length} arquivo(s) selado(s)</span> : 'PDF, JPG ou PNG — datado e selado com SHA-256'}
                </p>
              </div>
              <input ref={fileRef} type="file" className="hidden" accept="image/*,.pdf" onChange={handleUpload} />

              {arquivos.length > 0 && (
                <div className="mt-4 space-y-2">
                  {arquivos.map((a, i) => (
                    <div key={i} className="flex items-center justify-between gap-3 bg-white/[0.02] border border-white/5 rounded-sm px-4 py-2">
                      <span className="text-[11px] text-white/60 truncate">{a.nome}</span>
                      <span className="flex items-center gap-1.5 text-[9px] font-mono text-[#c5a059]/70 shrink-0" title={`SHA-256: ${a.hash}`}>
                        <Lock size={10} /> {a.hash.slice(0, 10)}…
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Observação */}
          <div className="p-5 bg-[#010c20]/60 border border-[#c5a059]/15 rounded-sm">
            <label className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-3">
              <AlertCircle size={14} /> Observações
            </label>
            <textarea
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm outline-none focus:border-[#c5a059] min-h-[70px] resize-none placeholder:text-white/15"
              placeholder="Notas, pontos de atenção ou contexto adicional..."
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
            />
          </div>
        </div>

        {/* Rodapé */}
        <div className="p-6 border-t border-[#c5a059]/20 bg-[#010c20] flex items-center justify-between shrink-0">
          <button onClick={onClose} className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 hover:text-[#c5a059] transition-colors">
            Cancelar
          </button>
          <button
            onClick={handleSalvar}
            disabled={enviando}
            className="px-10 py-4 bg-gradient-to-r from-[#c5a059] to-[#b38f4d] hover:from-[#d4b36d] hover:to-[#c5a059] text-[#010c20] font-black text-[10px] uppercase tracking-[0.3em] rounded-sm transition-all disabled:opacity-50 flex items-center gap-3"
          >
            {enviando ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Selar Registro
          </button>
        </div>
      </div>
    </div>
  )
}
