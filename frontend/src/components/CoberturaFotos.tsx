import { useState, useEffect } from 'react'
import { Ativo } from '../types'
import { api } from '../services/api'
import { ArrowLeft, Camera, Upload, Loader2, Lock, Download, ShieldCheck, MapPin } from 'lucide-react'
import { COBERTURA_CATS, MAX_FOTOS, COBERTURA_PREMIUM, normalizarCategoria } from '../config/coberturaFotos'
import { obterGeo } from '../utils/geo'

/* Cobertura fotográfica do dossiê — galeria organizada por categoria.
   Barra geral (total/400) + barra por categoria (count/mínimo). */
export default function CoberturaFotos({ ativo, onBack, readOnly = false }: { ativo: Ativo; onBack: () => void; readOnly?: boolean }) {
  const [fotos, setFotos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploadingCat, setUploadingCat] = useState<string | null>(null)

  const carregar = async () => {
    setLoading(true)
    try {
      const data = await api.documentos.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      // Pool de cobertura = fotos do ativo, exceto a vitrine (apresentação)
      setFotos(arr.filter((d: any) => d.tipo === 'foto' && d.categoria !== 'vitrine'))
    } catch {
      setFotos([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() /* eslint-disable-next-line */ }, [ativo.id])

  // Agrupa por categoria de cobertura
  const porCat: Record<string, any[]> = {}
  for (const c of COBERTURA_CATS) porCat[c.key] = []
  for (const f of fotos) (porCat[normalizarCategoria(f.categoria)] ||= []).push(f)

  const total = fotos.length
  const pctGeral = Math.min(100, Math.round((total / MAX_FOTOS) * 100))
  const lotado = total >= MAX_FOTOS
  const premium = pctGeral >= COBERTURA_PREMIUM

  const handleUpload = async (catKey: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    const espaco = MAX_FOTOS - total
    if (espaco <= 0) { e.target.value = ''; return }
    const lote = files.slice(0, espaco)
    setUploadingCat(catKey)
    try {
      const geo = await obterGeo() // GPS do dispositivo (com permissão); null se negado
      for (const file of lote) {
        const fd = new FormData()
        fd.append('file', file)
        await api.documentos.upload(ativo.id, 'foto', `galeria_${catKey}`, fd, geo)
      }
      await carregar()
    } catch {
      alert('Falha no upload. O primeiro envio pode levar ~20s (servidor acordando). Tente novamente.')
    } finally {
      setUploadingCat(null)
      e.target.value = ''
    }
  }

  // Cor da barra geral conforme o nível de cobertura
  const barGeral = premium
    ? 'bg-gradient-to-r from-emerald-400 to-emerald-300'
    : pctGeral >= 40
      ? 'bg-gradient-to-r from-[#c5a059] to-[#E5D5B7]'
      : 'bg-gradient-to-r from-amber-500 to-amber-400'

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
          <ArrowLeft size={16} />
        </button>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <Camera size={20} className="text-[#c5a059]" /> Registro Fotográfico
          <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· Cobertura do Dossiê</span>
        </h2>
      </div>

      {/* ===== Barra geral de cobertura ===== */}
      <div className="bg-[#021431] border border-white/10 rounded-sm p-6 space-y-4">
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40">Cobertura do Dossiê</p>
            <p className="text-2xl font-serif font-bold text-white mt-1">
              {total}<span className="text-white/30 text-lg"> / {MAX_FOTOS}</span>
              <span className={`ml-3 text-lg ${premium ? 'text-emerald-400' : pctGeral >= 40 ? 'text-[#c5a059]' : 'text-amber-400'}`}>{pctGeral}%</span>
            </p>
          </div>
          {premium && (
            <span className="flex items-center gap-2 px-4 py-2 rounded-sm text-[9px] font-black uppercase tracking-[0.2em] border border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
              <ShieldCheck size={13} /> Cobertura Premium
            </span>
          )}
        </div>
        <div className="h-3 bg-white/5 rounded-full overflow-hidden shadow-inner">
          <div className={`h-full rounded-full transition-all duration-1000 ${barGeral}`} style={{ width: `${pctGeral}%` }} />
        </div>
        <p className="text-white/30 text-[10px] tracking-wide">
          {premium
            ? 'Cobertura premium (≥ 80%) — peso elevado na negociação e na seguradora.'
            : `Faltam ${MAX_FOTOS - total} fotos para o máximo. A partir de ${COBERTURA_PREMIUM}% o dossiê ganha peso premium na negociação.`}
        </p>
      </div>

      {/* ===== Cobertura por categoria ===== */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-4">
          {COBERTURA_CATS.map((c) => {
            const arr = porCat[c.key] || []
            const n = arr.length
            const pct = Math.min(100, Math.round((n / c.minimo) * 100))
            const completo = n >= c.minimo
            const subindo = uploadingCat === c.key
            return (
              <div key={c.key} className="bg-[#021431] border border-white/5 rounded-sm p-5 space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <p className="text-white text-sm font-bold tracking-wide truncate">{c.label}</p>
                      <span className={`text-[10px] font-black uppercase tracking-[0.15em] tabular-nums shrink-0 ${completo ? 'text-emerald-400' : 'text-white/40'}`}>
                        {n} / {c.minimo}{completo && ' ✓'}
                      </span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden shadow-inner">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${completo ? 'bg-gradient-to-r from-emerald-400 to-emerald-300' : 'bg-gradient-to-r from-[#c5a059] to-[#E5D5B7]'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  {!readOnly && (
                  <label className={`shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-sm text-[10px] font-black uppercase tracking-[0.15em] border transition-all ${
                    lotado ? 'border-white/10 text-white/20 cursor-not-allowed' :
                    subindo ? 'border-[#c5a059]/40 bg-[#c5a059]/5 text-[#c5a059] cursor-default' :
                    'border-[#c5a059]/30 text-[#c5a059] hover:bg-[#c5a059] hover:text-[#010c20] cursor-pointer'
                  }`}>
                    <input type="file" className="hidden" multiple accept="image/png,image/jpeg" disabled={lotado || subindo} onChange={(e) => handleUpload(c.key, e)} />
                    {subindo ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
                    {subindo ? 'Enviando' : 'Adicionar'}
                  </label>
                  )}
                </div>

                {arr.length > 0 && (
                  <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2.5">
                    {arr.map((f) => (
                      <div key={f.id} className="group relative rounded-sm overflow-hidden border border-white/10 aspect-square bg-[#010c20]">
                        <img src={f.url_arquivo} alt={f.nome_arquivo} className="w-full h-full object-cover" loading="lazy" />
                        <a href={f.url_arquivo} target="_blank" rel="noopener noreferrer" download className="absolute inset-0 flex items-center justify-center bg-[#010c20]/0 group-hover:bg-[#010c20]/70 opacity-0 group-hover:opacity-100 transition-all">
                          <Download size={15} className="text-[#c5a059]" />
                        </a>
                        <span className="absolute bottom-0 right-0 bg-[#010c20]/80 text-[#c5a059] p-1"><Lock size={8} /></span>
                        {f.latitude != null && f.longitude != null && (
                          <span className="absolute top-1 left-1 bg-[#010c20]/80 text-emerald-400 p-1 rounded-sm" title={`Geolocalizada: ${Number(f.latitude).toFixed(5)}, ${Number(f.longitude).toFixed(5)}`}>
                            <MapPin size={9} />
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      <p className="text-white/25 text-[10px] uppercase tracking-widest text-center pt-2">
        Cada foto é datada e selada com SHA-256 — imutável. Limite de {MAX_FOTOS} fotos por embarcação (vitrine à parte).
      </p>
    </div>
  )
}
