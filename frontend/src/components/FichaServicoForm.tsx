import { useEffect, useMemo, useRef, useState } from 'react'
import { Loader2, Upload, Lock, ShieldCheck, AlertCircle, Trash2 } from 'lucide-react'
import { supabase, api } from '../services/api'
import type { ServicoConfig, ServicoField, ServicoUploadSlot } from '../config/servicosCategorias'

interface SealedFile { slot: string; nome: string; url: string; hash: string; tamanho: number }

interface Props {
  categoriaKey: string
  categoriaTitulo: string
  ativoId: string
  config: ServicoConfig
  onSaved: () => void
  onCancel: () => void
}

// Mapeia o status legível -> enum aceito pelo backend de registros
const STATUS_ENUM: Record<string, string> = {
  'Concluído': 'concluido',
  'Pendente': 'pendente',
  'Atenção': 'atencao',
}

export default function FichaServicoForm({ categoriaKey, categoriaTitulo, ativoId, config, onSaved, onCancel }: Props) {
  const [campos, setCampos] = useState<Record<string, string>>({})
  const [evidencias, setEvidencias] = useState<SealedFile[]>([])
  const [subindo, setSubindo] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erros, setErros] = useState<string[]>([])
  const [enviadoPor, setEnviadoPor] = useState<string>('')
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({})

  // "Quem enviou" — capturado automaticamente da sessão (imutável)
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setEnviadoPor(data.user?.email || data.user?.id || 'usuário autenticado')
    }).catch(() => setEnviadoPor('usuário autenticado'))
  }, [])

  const setCampo = (key: string, value: string) => setCampos((p) => ({ ...p, [key]: value }))

  const condOk = (cond?: { key: string; equals?: string; truthy?: boolean }) => {
    if (!cond) return true
    const v = campos[cond.key]
    if (cond.truthy) return Boolean(v && String(v).trim() && Number(v) !== 0)
    return v === cond.equals
  }

  const camposVisiveis = useMemo(() => config.fields.filter((f) => condOk(f.showIf)), [config.fields, campos])
  const uploadsVisiveis = useMemo(() => config.uploads.filter((u) => condOk(u.showIf)), [config.uploads, campos])

  const sha256Hex = async (file: File): Promise<string> => {
    const buf = await file.arrayBuffer()
    const digest = await crypto.subtle.digest('SHA-256', buf)
    return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('')
  }

  const handleUpload = async (slot: ServicoUploadSlot, files: FileList | null) => {
    if (!files || !files.length) return
    setSubindo(slot.key)
    try {
      const novos: SealedFile[] = []
      for (const file of Array.from(files)) {
        const hash = await sha256Hex(file)
        const ext = file.name.split('.').pop()
        const path = `${ativoId}/${categoriaKey}/${slot.key}/${Date.now()}-${Math.round(performance.now())}.${ext}`
        const { error } = await supabase.storage.from('media').upload(path, file, { upsert: false })
        if (error) throw error
        const { data } = supabase.storage.from('media').getPublicUrl(path)
        if (data?.publicUrl) novos.push({ slot: slot.key, nome: file.name, url: data.publicUrl, hash, tamanho: file.size })
      }
      // Slot único substitui; slot múltiplo acumula
      setEvidencias((prev) => slot.multiple ? [...prev, ...novos] : [...prev.filter((e) => e.slot !== slot.key), ...novos])
    } catch (err: any) {
      alert('Erro no upload: ' + (err?.message || err))
    } finally {
      setSubindo(null)
      const ref = fileRefs.current[slot.key]
      if (ref) ref.value = ''
    }
  }

  const removerEvidencia = (url: string) => setEvidencias((p) => p.filter((e) => e.url !== url))

  const validar = (): string[] => {
    const e: string[] = []
    for (const f of camposVisiveis) {
      if (f.required && !String(campos[f.key] || '').trim()) e.push(`Campo obrigatório: ${f.label}`)
    }
    for (const u of uploadsVisiveis) {
      const obrig = u.required || (u.requiredIf && condOk(u.requiredIf))
      const temArquivo = evidencias.some((ev) => ev.slot === u.key)
      if (obrig && !temArquivo) e.push(`Evidência obrigatória: ${u.label}`)
    }
    return e
  }

  const selar = async () => {
    const e = validar()
    setErros(e)
    if (e.length) return
    setEnviando(true)
    try {
      const statusEnum = STATUS_ENUM[campos.status] || 'registrado'
      await api.registros.create({
        ativo_id: ativoId,
        categoria: categoriaKey,
        titulo: (campos.servico || campos.titulo || categoriaTitulo).slice(0, 120),
        observacao: campos.observacao || undefined,
        dados: {
          ...campos,
          evidencias,
          enviado_por: enviadoPor,
          enviado_em: new Date().toISOString(),
        },
        status: statusEnum as any,
      })
      onSaved()
    } catch (err: any) {
      alert('Não foi possível selar o registro: ' + (err?.message || err))
    } finally {
      setEnviando(false)
    }
  }

  const inputCls = 'w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20'

  const renderField = (f: ServicoField) => {
    if (f.type === 'select') {
      return (
        <select className={inputCls + ' appearance-none'} value={campos[f.key] || ''} onChange={(ev) => setCampo(f.key, ev.target.value)}>
          <option value="" className="bg-[#010c20]">Selecione</option>
          {f.options?.map((o) => <option key={o} value={o} className="bg-[#010c20]">{o}</option>)}
        </select>
      )
    }
    if (f.type === 'textarea') {
      return <textarea className={inputCls + ' resize-none'} rows={2} placeholder={f.placeholder} value={campos[f.key] || ''} onChange={(ev) => setCampo(f.key, ev.target.value)} />
    }
    return (
      <div className="relative">
        <input type={f.type} className={inputCls + (f.suffix ? ' pr-12' : '')} placeholder={f.placeholder} value={campos[f.key] || ''} onChange={(ev) => setCampo(f.key, ev.target.value)} />
        {f.suffix && <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-black uppercase tracking-widest text-white/30">{f.suffix}</span>}
      </div>
    )
  }

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); selar() }}
      className="bg-[#021431] border border-[#c5a059]/20 rounded-sm p-6 space-y-8 animate-in slide-in-from-top-2 duration-300"
    >
      {/* Selo de custódia */}
      <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059]">
        <ShieldCheck size={14} /> Ficha de Serviço · selada e imutável
        <span className="text-white/25 normal-case tracking-normal font-medium ml-auto flex items-center gap-1.5">
          <Lock size={11} /> Enviado por {enviadoPor || '...'}
        </span>
      </div>

      {/* Campos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {camposVisiveis.map((f) => (
          <div key={f.key} className={`space-y-1.5 ${f.full ? 'md:col-span-3' : ''}`}>
            <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">
              {f.label} {f.required && <span className="text-[#c5a059]">*</span>}
            </label>
            {renderField(f)}
          </div>
        ))}
      </div>

      {/* Evidências (upload selado) */}
      <div className="space-y-4">
        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#c5a059]">Evidências · SHA-256</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {uploadsVisiveis.map((u) => {
            const arquivos = evidencias.filter((e) => e.slot === u.key)
            const obrig = u.required || (u.requiredIf && condOk(u.requiredIf))
            return (
              <div key={u.key} className="space-y-2">
                <label className="block border border-dashed border-white/10 rounded-sm p-5 text-center cursor-pointer hover:border-[#c5a059]/50 bg-white/[0.01] transition-all">
                  <input
                    ref={(el) => { fileRefs.current[u.key] = el }}
                    type="file" className="hidden" accept={u.accept} multiple={u.multiple}
                    disabled={subindo === u.key}
                    onChange={(e) => handleUpload(u, e.target.files)}
                  />
                  {subindo === u.key ? (
                    <Loader2 size={20} className="mx-auto text-[#c5a059] animate-spin" />
                  ) : (
                    <Upload size={20} className="mx-auto text-white/20 mb-1.5" />
                  )}
                  <p className="text-[11px] text-white font-bold mt-1">
                    {u.label} {obrig && <span className="text-[#c5a059]">*</span>}
                  </p>
                  {u.hint && <p className="text-[9px] text-white/30 uppercase tracking-widest mt-0.5">{u.hint}</p>}
                </label>
                {arquivos.map((a) => (
                  <div key={a.url} className="flex items-center justify-between gap-2 bg-white/[0.02] border border-white/5 rounded-sm px-3 py-2">
                    <span className="text-[10px] text-white/60 truncate">{a.nome}</span>
                    <span className="flex items-center gap-2 shrink-0">
                      <span className="flex items-center gap-1 text-[9px] font-mono text-[#c5a059]/70" title={`SHA-256: ${a.hash}`}><Lock size={9} />{a.hash.slice(0, 8)}…</span>
                      <button type="button" onClick={() => removerEvidencia(a.url)} className="text-white/25 hover:text-rose-400"><Trash2 size={13} /></button>
                    </span>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>

      {/* Erros da trava forte */}
      {erros.length > 0 && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-sm p-4 space-y-1">
          <p className="flex items-center gap-2 text-rose-300 text-[10px] font-black uppercase tracking-widest"><AlertCircle size={13} /> Faltam evidências para selar</p>
          {erros.map((e) => <p key={e} className="text-rose-300/80 text-[11px]">• {e}</p>)}
        </div>
      )}

      {/* Ações */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <button type="button" onClick={onCancel} className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 hover:text-[#c5a059] transition-colors">
          Cancelar
        </button>
        <button type="submit" disabled={enviando} className="flex items-center gap-3 bg-gradient-to-r from-[#c5a059] to-[#b38f4d] hover:from-[#d4b36d] hover:to-[#c5a059] text-[#010c20] px-8 py-3.5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all disabled:opacity-50">
          {enviando ? <Loader2 size={15} className="animate-spin" /> : <Lock size={15} />}
          Selar Registro
        </button>
      </div>
    </form>
  )
}
