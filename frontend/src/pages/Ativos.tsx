import { useState, useEffect, useMemo } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, Archive, Anchor, Filter, Search, ChevronRight, X, Upload, Camera, Check, Loader2, Lock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'
import AtivoHub from '../components/AtivoHub'
import { obterGeo } from '../utils/geo'

// Categorias da galeria fotográfica da embarcação (organizada + sai no dossiê)
const GALERIA_CATS: { key: string; label: string }[] = [
  { key: 'casco_exterior', label: 'Casco / Exterior' },
  { key: 'motor', label: 'Motor / Propulsão' },
  { key: 'pintura', label: 'Pintura' },
  { key: 'interior', label: 'Interior' },
  { key: 'eletronica', label: 'Eletrônica / Navegação' },
  { key: 'notas_fiscais', label: 'Notas Fiscais' },
  { key: 'antes_depois', label: 'Antes e Depois' },
  { key: 'outros', label: 'Outros' },
]

export default function Ativos() {
  const { t } = useTranslation()
  const location = useLocation()
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [selectedAtivo, setSelectedAtivo] = useState<Ativo | null>(null)
  const [formData, setFormData] = useState({
    tipo: 'iate',
    marca: '',
    modelo: '',
    comprimento_pes: 0,
    ano_fabricacao: new Date().getFullYear(),
    // Contato do dono: é a chave de acesso dele ao Portal do Proprietário.
    // Ele entra digitando o e-mail, recebe um código e vê só o barco dele —
    // nunca a conta da marina, nunca a frota dos outros clientes.
    proprietario_email: '',
    proprietario_telefone: '',
  })
  // Galeria inicial organizada por categoria (até 400 fotos por embarcação)
  const MAX_FOTOS = 400
  const [novoAtivo, setNovoAtivo] = useState<Ativo | null>(null)
  const [galeria, setGaleria] = useState<Record<string, any[]>>({})
  const [catAtiva, setCatAtiva] = useState<string>(GALERIA_CATS[0].key)
  const [uploadingFotos, setUploadingFotos] = useState(false)
  const totalFotos = Object.values(galeria).reduce((a, b) => a + b.length, 0)
  // Vitrine: fotos de apresentação (interior/exterior) — até 30, SEPARADAS das 400
  const MAX_VITRINE = 30
  const [vitrineFiles, setVitrineFiles] = useState<File[]>([])
  const [salvando, setSalvando] = useState(false)
  const vitrinePreviews = useMemo(() => vitrineFiles.map((f) => URL.createObjectURL(f)), [vitrineFiles])
  useEffect(() => () => { vitrinePreviews.forEach((u) => URL.revokeObjectURL(u)) }, [vitrinePreviews])

  useEffect(() => {
    if (location.state && (location.state as any).openForm) {
      setShowForm(true)
    }
  }, [location.state])

  useEffect(() => {
    loadAtivos()
  }, [])

  // Carrega APENAS dados reais do banco (sem mock). Lista vazia => estado vazio.
  const loadAtivos = async () => {
    setLoading(true)
    try {
      const data = await api.ativos.list()
      setAtivos(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Erro ao carregar ativos:', err)
      setAtivos([])
    } finally {
      setLoading(false)
    }
  }

  const handleVitrineSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setVitrineFiles((prev) => {
      const merged = [...prev, ...files]
      if (merged.length > MAX_VITRINE) {
        alert(`Máximo de ${MAX_VITRINE} fotos de apresentação. As excedentes foram ignoradas.`)
      }
      return merged.slice(0, MAX_VITRINE)
    })
    e.target.value = ''
  }
  const removeVitrine = (idx: number) => setVitrineFiles((prev) => prev.filter((_, i) => i !== idx))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSalvando(true)
    try {
      const created = await api.ativos.create(formData)
      // Fotos de apresentação (vitrine) — enviadas com categoria 'vitrine',
      // separadas da galeria documental de 400.
      if (created?.id && vitrineFiles.length) {
        const geo = await obterGeo() // GPS do dispositivo (com permissão); null se negado
        for (const file of vitrineFiles) {
          const fd = new FormData()
          fd.append('file', file)
          await api.documentos.upload(created.id, 'foto', 'vitrine', fd, geo)
        }
      }
      setVitrineFiles([])
      setShowForm(false)
      setFormData({
        tipo: 'iate', marca: '', modelo: '', comprimento_pes: 0,
        ano_fabricacao: new Date().getFullYear(),
        proprietario_email: '', proprietario_telefone: '',
      })
      loadAtivos()
      // Etapa de fotos: galeria inicial organizada da embarcação recém-criada
      if (created?.id) {
        setNovoAtivo(created)
        setGaleria({})
        setCatAtiva(GALERIA_CATS[0].key)
      }
    } catch (err) {
      console.error('Erro ao criar:', err)
      alert('Não foi possível cadastrar a embarcação. Verifique a conexão com o servidor.')
    } finally {
      setSalvando(false)
    }
  }

  const recarregarGaleria = async (ativoId: string) => {
    const data = await api.documentos.list(ativoId)
    const grp: Record<string, any[]> = {}
    ;(Array.isArray(data) ? data : []).forEach((d: any) => {
      const cat = String(d.categoria || '')
      if (cat.startsWith('galeria_')) {
        const k = cat.replace('galeria_', '')
        ;(grp[k] = grp[k] || []).push(d)
      }
    })
    setGaleria(grp)
  }

  const handleFotos = async (catKey: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length || !novoAtivo) return
    const espaco = MAX_FOTOS - totalFotos
    if (espaco <= 0) { e.target.value = ''; return }
    const lote = files.slice(0, espaco)
    setUploadingFotos(true)
    try {
      const geo = await obterGeo() // GPS do dispositivo (com permissão); null se negado
      for (const file of lote) {
        const fd = new FormData()
        fd.append('file', file)
        await api.documentos.upload(novoAtivo.id, 'foto', `galeria_${catKey}`, fd, geo)
      }
      await recarregarGaleria(novoAtivo.id)
    } catch {
      alert('Falha no upload. O primeiro envio pode levar ~20s (servidor acordando). Tente novamente.')
    } finally {
      setUploadingFotos(false)
      e.target.value = ''
    }
  }

  const concluirGaleria = () => { setNovoAtivo(null); setGaleria({}) }

  /**
   * Arquiva a embarcação. NÃO exclui: os registros selados são a cadeia de
   * custódia e permanecem íntegros — é isso que dá valor ao dossiê.
   */
  const handleArquivar = async (id: string) => {
    const ok = confirm(
      'Arquivar esta embarcação?\n\n' +
      'Ela sai da operação, mas o histórico selado é preservado — registros ' +
      'da cadeia de custódia não podem ser excluídos.'
    )
    if (!ok) return
    try {
      await api.ativos.arquivar(id)
      loadAtivos()
    } catch (err) {
      console.error('Erro ao arquivar:', err)
      alert('Não foi possível arquivar. Verifique a conexão com o servidor.')
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4"></div>
        <span className="text-white/40 uppercase tracking-[0.2em] text-[10px] font-black">{t('common.loading')}</span>
      </div>
    )
  }

  return (
    <div className="space-y-10 animate-in fade-in duration-1000">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 border-b border-white/5 pb-10">
        <div>
          <h1 className="text-4xl font-serif font-bold text-white tracking-tight flex items-center gap-4">
             <Anchor size={28} className="text-[#c5a059]" />
             {t('common.assets')}
          </h1>
          <p className="text-white/30 text-[10px] mt-2 uppercase tracking-[0.4em] font-black">
             Protocolo do Sistema <span className="text-[#c5a059] mx-2">•</span> Console de Gestão
          </p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); setSelectedAtivo(null); }}
          className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 shadow-xl shadow-[#c5a059]/10"
        >
          {showForm ? <X size={18} /> : <Plus size={18} />}
          {showForm ? 'Fechar Cadastro' : t('common.new_asset')}
        </button>
      </div>

      {showForm && (
        <div
          className="p-10 rounded-sm animate-in slide-in-from-top-6 duration-700 shadow-2xl border border-white/5 relative overflow-hidden"
          style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#c5a059]/5 blur-[100px] rounded-full pointer-events-none"></div>

          <div className="flex items-center justify-between mb-10 relative z-10">
            <h3 className="text-xl font-serif font-bold text-white tracking-tight uppercase">Cadastro de Nova Embarcação</h3>
            <div className="h-px flex-1 bg-white/5 mx-8"></div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8 relative z-10">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { label: 'Tipo de Embarcação', key: 'tipo', type: 'select', options: ['iate', 'lancha', 'veleiro', 'jetski'] },
                { label: 'Fabricante / Marca', key: 'marca', type: 'text', placeholder: 'Azimut, Sunseeker...' },
                { label: 'Modelo', key: 'modelo', type: 'text', placeholder: 'Flybridge 78...' },
                { label: t('common.length_feet'), key: 'comprimento_pes', type: 'number', min: 0, max: 500, placeholder: 'Ex: 45' },
                { label: 'Ano de Fabricação', key: 'ano_fabricacao', type: 'number', min: 1900, max: new Date().getFullYear() },
                { label: 'E-mail do Proprietário', key: 'proprietario_email', type: 'email', placeholder: 'dono@email.com' },
                { label: 'WhatsApp do Proprietário', key: 'proprietario_telefone', type: 'text', placeholder: '(12) 99999-9999' }
              ].map((field) => (
                <div key={field.key} className="space-y-3 group">
                  <label className="text-[10px] uppercase tracking-[0.3em] text-white/30 font-black group-focus-within:text-[#c5a059] transition-colors">{field.label}</label>
                  {field.type === 'select' ? (
                    <select
                      value={formData[field.key as keyof typeof formData]}
                      onChange={(e) => setFormData({...formData, [field.key]: e.target.value})}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none appearance-none transition-all text-sm font-medium"
                    >
                      {field.options?.map(opt => (
                        <option key={opt} value={opt} className="bg-[#010c20] capitalize">{opt}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type={field.type}
                      value={formData[field.key as keyof typeof formData]}
                      onChange={(e) => setFormData({...formData, [field.key]: field.type === 'number' ? parseInt(e.target.value) : e.target.value})}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all text-sm font-medium placeholder:text-white/10"
                      placeholder={field.placeholder}
                      min={field.min}
                      max={field.max}
                      required
                    />
                  )}
                </div>
              ))}
            </div>
            {/* Fotos de apresentação (vitrine) — interior e exterior, separadas das 400 */}
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div>
                  <label className="text-[10px] uppercase tracking-[0.3em] text-white/40 font-black flex items-center gap-2">
                    <Camera size={13} className="text-[#c5a059]" /> Fotos da Embarcação · Interior e Exterior
                  </label>
                  <p className="text-white/25 text-[10px] mt-1.5 tracking-wide">
                    Imagens de apresentação da embarcação. <span className="text-[#c5a059]/80 font-bold">Separadas da galeria documental de {MAX_FOTOS} fotos.</span>
                  </p>
                </div>
                <span className={`text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1.5 rounded-sm border ${
                  vitrineFiles.length >= MAX_VITRINE ? 'text-rose-400 border-rose-400/30 bg-rose-400/10' : 'text-[#c5a059] border-[#c5a059]/20 bg-[#c5a059]/10'
                }`}>
                  {vitrineFiles.length} / {MAX_VITRINE}
                </span>
              </div>

              <label className={`block border border-dashed rounded-sm p-8 text-center transition-all ${
                vitrineFiles.length >= MAX_VITRINE ? 'border-white/10 opacity-40 pointer-events-none' : 'border-white/10 hover:border-[#c5a059]/50 bg-white/[0.02] cursor-pointer'
              }`}>
                <input type="file" className="hidden" multiple accept="image/png,image/jpeg" disabled={vitrineFiles.length >= MAX_VITRINE} onChange={handleVitrineSelect} />
                {vitrineFiles.length >= MAX_VITRINE ? (
                  <p className="text-white/50 text-xs font-black uppercase tracking-widest">Limite de {MAX_VITRINE} fotos de apresentação atingido</p>
                ) : (
                  <>
                    <Upload size={26} className="mx-auto text-white/15 mb-3" />
                    <p className="text-white text-xs font-black uppercase tracking-widest mb-1">Adicionar fotos de apresentação</p>
                    <p className="text-white/25 text-[10px] uppercase tracking-widest">PNG ou JPG · interior e exterior · restam {MAX_VITRINE - vitrineFiles.length}</p>
                  </>
                )}
              </label>

              {vitrineFiles.length > 0 && (
                <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
                  {vitrinePreviews.map((url, i) => (
                    <div key={url} className="group relative rounded-sm overflow-hidden border border-white/10 aspect-square bg-[#010c20]">
                      <img src={url} alt={`Apresentação ${i + 1}`} className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={() => removeVitrine(i)}
                        className="absolute top-1 right-1 w-6 h-6 flex items-center justify-center bg-[#010c20]/80 text-white/60 hover:text-rose-400 rounded-sm opacity-0 group-hover:opacity-100 transition-all"
                        title="Remover"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-6 pt-6">
              <button type="submit" disabled={salvando} className="bg-[#c5a059] text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] shadow-xl hover:bg-[#b38f4d] disabled:opacity-50 transition-all flex items-center gap-3">
                {salvando ? <Loader2 size={15} className="animate-spin" /> : null}
                {salvando ? 'Salvando...' : 'Confirmar Cadastro'}
              </button>
              <button type="button" onClick={() => setShowForm(false)} disabled={salvando} className="text-white/30 hover:text-white px-8 py-4 text-[10px] font-black uppercase tracking-[0.3em] transition-all disabled:opacity-30">Cancelar</button>
            </div>
          </form>
        </div>
      )}

      {/* Galeria organizada por categoria — até 400 fotos, sai no dossiê */}
      {novoAtivo && (() => {
        const cheio = totalFotos >= MAX_FOTOS
        const fotosCat = galeria[catAtiva] || []
        return (
          <div className="p-10 rounded-sm border border-[#c5a059]/25 bg-[#021431] animate-in slide-in-from-top-4 duration-500 space-y-6">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
                  <Camera size={20} className="text-[#c5a059]" /> Galeria da Embarcação
                </h3>
                <p className="text-white/40 text-[10px] mt-1.5 uppercase tracking-[0.3em] font-black">
                  {novoAtivo.marca} {novoAtivo.modelo} · organizada por categoria · sai no dossiê
                </p>
              </div>
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] bg-[#c5a059]/10 border border-[#c5a059]/20 px-4 py-2 rounded-sm">
                {totalFotos} / {MAX_FOTOS}
              </span>
            </div>

            {/* Abas de categoria */}
            <div className="flex flex-wrap gap-2">
              {GALERIA_CATS.map((c) => {
                const n = (galeria[c.key] || []).length
                const on = c.key === catAtiva
                return (
                  <button
                    key={c.key}
                    onClick={() => setCatAtiva(c.key)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-sm text-[10px] font-black uppercase tracking-[0.15em] border transition-all ${
                      on ? 'bg-[#c5a059] text-[#010c20] border-[#c5a059]' : 'text-white/50 border-white/10 hover:border-[#c5a059]/40 hover:text-white/80'
                    }`}
                  >
                    {c.label}
                    {n > 0 && <span className={`px-1.5 rounded-sm ${on ? 'bg-[#010c20]/20' : 'bg-[#c5a059]/15 text-[#c5a059]'}`}>{n}</span>}
                  </button>
                )
              })}
            </div>

            {/* Upload da categoria ativa */}
            <label className={`block border border-dashed rounded-sm p-8 text-center transition-all ${
              uploadingFotos ? 'border-[#c5a059]/40 bg-[#c5a059]/5 pointer-events-none' :
              cheio ? 'border-white/10 opacity-40 pointer-events-none' :
              'border-white/10 hover:border-[#c5a059]/50 bg-white/[0.02] cursor-pointer'
            }`}>
              <input type="file" className="hidden" multiple accept="image/png,image/jpeg" disabled={uploadingFotos || cheio} onChange={(e) => handleFotos(catAtiva, e)} />
              {uploadingFotos ? (
                <div className="flex flex-col items-center">
                  <Loader2 size={26} className="text-[#c5a059] animate-spin mb-3" />
                  <span className="text-[10px] font-black text-[#c5a059] uppercase tracking-widest">Enviando e selando (SHA-256)...</span>
                </div>
              ) : cheio ? (
                <p className="text-white/50 text-xs font-black uppercase tracking-widest">Limite de {MAX_FOTOS} fotos atingido</p>
              ) : (
                <>
                  <Upload size={28} className="mx-auto text-white/15 mb-3" />
                  <p className="text-white text-xs font-black uppercase tracking-widest mb-1">Adicionar em "{GALERIA_CATS.find((c) => c.key === catAtiva)?.label}"</p>
                  <p className="text-white/25 text-[10px] uppercase tracking-widest">PNG ou JPG · várias de uma vez · restam {MAX_FOTOS - totalFotos}</p>
                </>
              )}
            </label>

            {/* Fotos da categoria ativa */}
            {fotosCat.length > 0 && (
              <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-3">
                {fotosCat.map((f) => (
                  <div key={f.id} className="relative rounded-sm overflow-hidden border border-white/10 aspect-square bg-[#010c20]">
                    <img src={f.url_arquivo} alt={f.nome_arquivo} className="w-full h-full object-cover" loading="lazy" />
                    <span className="absolute bottom-0 right-0 bg-[#010c20]/80 text-[#c5a059] p-1"><Lock size={9} /></span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center justify-between gap-4 pt-2 border-t border-white/5">
              <p className="text-white/30 text-[10px] uppercase tracking-widest">Cada foto é datada e selada com SHA-256 — imutável. Aparece no dossiê na sua categoria.</p>
              <button onClick={concluirGaleria} className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-8 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all">
                <Check size={15} /> Concluir
              </button>
            </div>
          </div>
        )
      })()}

      {!selectedAtivo ? (
        <>
          {/* Barra de Busca e Filtro */}
          <div className="bg-white/[0.01] border border-white/5 p-6 rounded-sm flex flex-wrap items-center justify-between gap-6 shadow-xl">
             <div className="flex items-center gap-6 flex-1 min-w-[200px]">
                <div className="relative flex-1 group">
                   <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-white/10 group-focus-within:text-[#c5a059] transition-all" size={18} />
                   <input
                     type="text"
                     placeholder="Buscar embarcação por nome, fabricante ou ID..."
                     className="w-full bg-white/[0.03] border border-white/10 rounded-sm pl-14 pr-6 py-4 text-[11px] font-medium text-white focus:border-[#c5a059]/40 outline-none transition-all placeholder:text-white/10"
                   />
                </div>
                <button className="flex items-center gap-3 text-white/30 hover:text-[#c5a059] transition-all text-[10px] font-black uppercase tracking-[0.3em] border border-white/10 px-8 py-4 rounded-sm">
                   <Filter size={16} />
                   Filtrar
                </button>
             </div>
          </div>

          {/* Tabela de Ativos */}
          <div className="bg-white/[0.01] border border-white/5 rounded-sm overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.01]">
                    <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20">Embarcação</th>
                    <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 hidden md:table-cell">Especificações</th>
                    <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 hidden sm:table-cell">Conformidade</th>
                    <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {ativos.map((ativo) => (
                    <tr key={ativo.id} className="group hover:bg-[#c5a059]/[0.02] transition-all duration-500">
                      <td className="py-8 px-8">
                        <div className="flex items-center gap-6 cursor-pointer" onClick={() => setSelectedAtivo(ativo)}>
                          <div className="w-16 h-16 bg-[#010c20] border border-white/10 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:border-[#c5a059]/50 group-hover:bg-[#021a3d] transition-all duration-700">
                            <Ship size={32} strokeWidth={1} />
                          </div>
                          <div className="min-w-0">
                            {/* O nome batizado manda. O painel mostrava só
                                marca+modelo, então a embarcação tinha um nome
                                no dossiê e outro aqui. */}
                            <div className="text-white font-serif font-bold text-xl tracking-tight group-hover:text-[#c5a059] transition-all duration-500">
                              {ativo.nome_reg || `${ativo.marca} ${ativo.modelo}`}
                            </div>
                            {ativo.nome_reg && (
                              <div className="text-white/35 text-[11px] mt-0.5">
                                {ativo.marca} {ativo.modelo}
                              </div>
                            )}
                            <div className="text-[9px] text-white/20 font-black uppercase tracking-[0.3em] mt-1.5 flex items-center gap-2">
                               <span className="w-1.5 h-1.5 rounded-full bg-white/5 group-hover:bg-[#c5a059] transition-colors"></span>
                               ID: #{String(ativo.id).slice(0, 8).toUpperCase()}
                            </div>
                            {/* Medidor de fotos da embarcação (0–200) */}
                            {(() => {
                              const n = ativo.total_fotos || 0
                              const pct = Math.min(100, (n / MAX_FOTOS) * 100)
                              return (
                                <div className="mt-2.5 flex items-center gap-2 max-w-[200px]" title={`${n} de ${MAX_FOTOS} fotos`}>
                                  <Camera size={11} className="text-white/25 shrink-0" />
                                  <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden shadow-inner">
                                    <div
                                      className={`h-full rounded-full transition-all duration-1000 ${n >= MAX_FOTOS ? 'bg-rose-400/80' : 'bg-gradient-to-r from-[#c5a059] to-[#E5D5B7]'}`}
                                      style={{ width: `${pct}%` }}
                                    />
                                  </div>
                                  <span className="text-[9px] font-black text-white/35 tabular-nums shrink-0">{n}/{MAX_FOTOS}</span>
                                </div>
                              )
                            })()}
                          </div>
                        </div>
                      </td>
                      <td className="py-8 px-8 hidden md:table-cell">
                        <div className="space-y-1.5">
                          <div className="text-xs text-white/60 font-bold uppercase tracking-widest capitalize">{ativo.tipo}</div>
                          <div className="text-[10px] text-white/20 uppercase tracking-[0.2em] font-medium">Fabricado em {ativo.ano_fabricacao}</div>
                        </div>
                      </td>
                      <td className="py-8 px-8 hidden sm:table-cell">
                        <div className="flex items-center gap-5">
                          <div className="flex-1 max-w-[120px] h-1.5 bg-white/5 rounded-full overflow-hidden shadow-inner">
                            <div
                              className="h-full bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] rounded-full shadow-[0_0_8px_rgba(197,160,89,0.3)] transition-all duration-1000"
                              style={{ width: `${ativo.progresso || 0}%` }}
                            />
                          </div>
                          <span className="text-xs font-black text-white/40">{ativo.progresso || 0}%</span>
                        </div>
                      </td>
                      <td className="py-8 px-8 text-right">
                        <div className="flex items-center justify-end gap-3">
                           <button
                             onClick={() => setSelectedAtivo(ativo)}
                             className="w-10 h-10 flex items-center justify-center border border-white/5 text-white/10 hover:text-[#c5a059] hover:border-[#c5a059]/30 rounded-sm transition-all"
                           >
                              <ChevronRight size={20} />
                           </button>
                           <button
                             onClick={() => handleArquivar(ativo.id)}
                             title="Arquivar embarcação (o histórico selado é preservado)"
                             aria-label="Arquivar embarcação"
                             className="w-10 h-10 flex items-center justify-center border border-white/5 text-white/10 hover:text-amber-400/60 hover:border-amber-400/25 rounded-sm transition-all"
                           >
                             <Archive size={18} />
                           </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {ativos.length === 0 && (
              <div className="text-center py-32 bg-white/[0.01]">
                <Ship size={64} strokeWidth={0.5} className="mx-auto text-white/5 mb-6" />
                <p className="text-white/30 uppercase tracking-[0.4em] text-[10px] font-black font-serif italic mb-2">Nenhuma embarcação cadastrada</p>
                <p className="text-white/15 text-xs">Clique em "{t('common.new_asset')}" para cadastrar a primeira.</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <AtivoHub ativo={selectedAtivo} onBack={() => setSelectedAtivo(null)} />
      )}
    </div>
  )
}
