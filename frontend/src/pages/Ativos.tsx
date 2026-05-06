import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, Trash2, Anchor, Filter, Search, ChevronRight, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Ativos() {
  const { t } = useTranslation()
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    tipo: 'iate',
    marca: '',
    modelo: '',
    comprimento_pes: 0,
    ano_fabricacao: new Date().getFullYear(),
  })
  
  useEffect(() => {
    loadAtivos()
  }, [])
  
  const loadAtivos = async () => {
    try {
      const data = await api.ativos.list()
      setAtivos(data)
    } catch (err) {
      console.error('Erro:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.ativos.create(formData)
      setShowForm(false)
      setFormData({ tipo: 'iate', marca: '', modelo: '', comprimento_pes: 0, ano_fabricacao: new Date().getFullYear() })
      loadAtivos()
    } catch (err) {
      console.error('Erro ao criar:', err)
    }
  }
  
  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this asset?')) {
      try {
        await api.ativos.delete(id)
        loadAtivos()
      } catch (err) {
        console.error('Erro ao excluir:', err)
      }
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
             System Protocol <span className="text-[#c5a059] mx-2">•</span> Management Console
          </p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 shadow-xl shadow-[#c5a059]/10"
        >
          {showForm ? <X size={18} /> : <Plus size={18} />}
          {showForm ? 'Close Registration' : t('common.new_asset')}
        </button>
      </div>
      
      {showForm && (
        <div 
          className="p-10 rounded-sm animate-in slide-in-from-top-6 duration-700 shadow-2xl border border-white/5 relative overflow-hidden"
          style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#c5a059]/5 blur-[100px] rounded-full pointer-events-none"></div>
          
          <div className="flex items-center justify-between mb-10 relative z-10">
            <h3 className="text-xl font-serif font-bold text-white tracking-tight uppercase">New Vessel Registration</h3>
            <div className="h-px flex-1 bg-white/5 mx-8"></div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-8 relative z-10">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { label: 'Vessel Type', key: 'tipo', type: 'select', options: ['iate', 'lancha', 'veleiro', 'jetski'] },
                { label: 'Manufacturer / Brand', key: 'marca', type: 'text', placeholder: 'Azimut, Sunseeker...' },
                { label: 'Model', key: 'modelo', type: 'text', placeholder: 'Flybridge 78...' },
                { label: t('common.length_feet'), key: 'comprimento_pes', type: 'number', min: 0, max: 500, placeholder: 'Ex: 45' },
                { label: 'Build Year', key: 'ano_fabricacao', type: 'number', min: 1900, max: new Date().getFullYear() }
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
            <div className="flex gap-6 pt-6">
              <button type="submit" className="bg-[#c5a059] text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] shadow-xl hover:bg-[#b38f4d] transition-all">Confirm Registration</button>
              <button type="button" onClick={() => setShowForm(false)} className="text-white/30 hover:text-white px-8 py-4 text-[10px] font-black uppercase tracking-[0.3em] transition-all">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="bg-white/[0.01] border border-white/5 p-6 rounded-sm flex flex-wrap items-center justify-between gap-6 shadow-xl">
         <div className="flex items-center gap-6 flex-1 min-w-[300px]">
            <div className="relative flex-1 group">
               <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-white/10 group-focus-within:text-[#c5a059] transition-all" size={18} />
               <input 
                 type="text" 
                 placeholder="Search vessels by name, manufacturer or ID..." 
                 className="w-full bg-white/[0.03] border border-white/10 rounded-sm pl-14 pr-6 py-4 text-[11px] font-medium text-white focus:border-[#c5a059]/40 outline-none transition-all placeholder:text-white/10"
               />
            </div>
            <button className="flex items-center gap-3 text-white/30 hover:text-[#c5a059] transition-all text-[10px] font-black uppercase tracking-[0.3em] border border-white/10 px-8 py-4 rounded-sm">
               <Filter size={16} />
               {t('lp.terms')}
            </button>
         </div>
      </div>
      
      {/* Table Container */}
      <div className="bg-white/[0.01] border border-white/5 rounded-sm overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.01]">
                <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20">Vessel Details</th>
                <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 hidden md:table-cell">Specifications</th>
                <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20">Tier Status</th>
                <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 hidden sm:table-cell">Compliance</th>
                <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {ativos.map((ativo) => (
                <tr key={ativo.id} className="group hover:bg-[#c5a059]/[0.02] transition-all duration-500">
                  <td className="py-8 px-8">
                    <div className="flex items-center gap-6">
                      <div className="w-16 h-16 bg-[#010c20] border border-white/10 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:border-[#c5a059]/50 group-hover:bg-[#021a3d] transition-all duration-700">
                        <Ship size={32} strokeWidth={1} />
                      </div>
                      <div>
                        <div className="text-white font-serif font-bold text-xl tracking-tight group-hover:text-[#c5a059] transition-all duration-500">{ativo.marca} {ativo.modelo}</div>
                        <div className="text-[9px] text-white/20 font-black uppercase tracking-[0.3em] mt-1.5 flex items-center gap-2">
                           <span className="w-1.5 h-1.5 rounded-full bg-white/5 group-hover:bg-[#c5a059] transition-colors"></span>
                           ID: #{ativo.id.slice(0, 8).toUpperCase()}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-8 px-8 hidden md:table-cell">
                    <div className="space-y-1.5">
                      <div className="text-xs text-white/60 font-bold uppercase tracking-widest">{ativo.tipo}</div>
                      <div className="text-[10px] text-white/20 uppercase tracking-[0.2em] font-medium">Built in {ativo.ano_fabricacao}</div>
                    </div>
                  </td>
                  <td className="py-8 px-8">
                    <span className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.3em] border shadow-xl ${
                      ativo.porte_categoria === 'superyacht' ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' :
                      ativo.porte_categoria === 'executive' ? 'bg-white/90 border-white text-[#010c20]' :
                      'bg-white/10 border-white/20 text-white/40'
                    }`}>
                      {t(`common.${ativo.porte_categoria}`)}
                    </span>
                  </td>
                  <td className="py-8 px-8 hidden sm:table-cell">
                    <div className="flex items-center gap-5">
                      <div className="flex-1 max-w-[120px] h-1.5 bg-white/5 rounded-full overflow-hidden shadow-inner">
                        <div 
                          className="h-full bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] rounded-full shadow-[0_0_8px_rgba(197,160,89,0.3)] transition-all duration-1000"
                          style={{ width: `${ativo.progresso}%` }}
                        />
                      </div>
                      <span className="text-xs font-black text-white/40">{ativo.progresso}%</span>
                    </div>
                  </td>
                  <td className="py-8 px-8 text-right">
                    <div className="flex items-center justify-end gap-3">
                       <button className="w-10 h-10 flex items-center justify-center border border-white/5 text-white/10 hover:text-[#c5a059] hover:border-[#c5a059]/30 rounded-sm transition-all">
                          <ChevronRight size={20} />
                       </button>
                       <button 
                         onClick={() => handleDelete(ativo.id)}
                         className="w-10 h-10 flex items-center justify-center border border-white/5 text-white/10 hover:text-red-400/50 hover:border-red-400/20 rounded-sm transition-all"
                       >
                         <Trash2 size={18} />
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
            <p className="text-white/10 uppercase tracking-[0.5em] text-[10px] font-black font-serif italic">{t('common.no_assets')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
