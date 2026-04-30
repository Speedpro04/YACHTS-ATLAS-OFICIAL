import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, CheckCircle, AlertCircle, TrendingUp, Shield, Anchor, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function Dashboard() {
  const { t } = useTranslation()
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadDashboard()
  }, [])
  
  const loadDashboard = async () => {
    try {
      const data = await api.ativos.list()
      setAtivos(data)
    } catch (err) {
      console.error('Erro ao carregar:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const stats = {
    total: ativos.length,
    gold: ativos.filter(a => a.classificacao === 'gold').length,
    compliance: Math.round(ativos.reduce((acc, curr) => acc + curr.progresso, 0) / (ativos.length || 1)),
    dossiers: 12, // Mocked for demo
    revenue: 4800, // Mocked for demo ($400 average * 12)
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
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* Welcome & Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div 
          className="lg:col-span-2 relative border border-white/5 p-12 rounded-sm overflow-hidden flex flex-col justify-between min-h-[350px] shadow-2xl"
          style={{ background: 'radial-gradient(circle at top right, #021a3d 0%, #010c20 100%)' }}
        >
          {/* Decorative glow */}
          <div className="absolute top-0 right-0 w-80 h-80 bg-[#c5a059]/5 blur-[120px] rounded-full pointer-events-none"></div>
          
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
               <div className="w-8 h-px bg-[#c5a059]"></div>
               <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#c5a059]">{t('auth.personal_security')}</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-serif font-bold text-white mb-6 tracking-tight leading-tight">
              {t('common.marina_hub')} <br />
              <span className="italic text-[#c5a059]">Fleet Excellence.</span>
            </h1>
            <p className="text-white/40 text-lg max-w-md leading-relaxed font-light">
              {t('lp.mission_tagline')}
            </p>
          </div>

          <div className="relative z-10 flex flex-wrap gap-6 mt-12">
            <button className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3 shadow-xl shadow-[#c5a059]/10">
              <Plus size={16} />
              {t('common.add_asset')}
            </button>
            <button className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3">
              <Download size={16} />
              Report
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {[
            { label: t('common.total_assets'), value: stats.total, icon: Ship, color: '#c5a059' },
            { label: t('common.generated_dossiers'), value: stats.dossiers, icon: Download, color: '#c5a059' },
            { label: t('common.total_revenue'), value: `$${stats.revenue}`, icon: TrendingUp, color: '#c5a059' }
          ].map((stat, i) => (
            <div key={i} className="bg-white/[0.02] border border-white/5 p-8 rounded-sm flex items-center gap-8 group hover:border-[#c5a059]/30 transition-all shadow-lg">
              <div className="w-16 h-16 bg-[#c5a059]/5 border border-[#c5a059]/10 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                <stat.icon size={28} strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-white/30 text-[10px] uppercase tracking-[0.3em] font-black mb-2">{stat.label}</p>
                <p className="text-4xl font-serif font-bold text-white tracking-tight">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Assets Section */}
      <div>
        <div className="flex items-center justify-between mb-12 border-b border-white/5 pb-8">
          <h2 className="text-2xl font-serif font-bold text-white flex items-center gap-4 tracking-tight">
            <Anchor size={24} className="text-[#c5a059]" />
            {t('common.your_assets')}
          </h2>
          <div className="flex gap-4">
            <div className="flex bg-white/5 border border-white/10 rounded-sm p-1 shadow-inner">
               <button className="px-6 py-1.5 text-[9px] font-black uppercase tracking-widest bg-[#c5a059] text-[#010c20] rounded-sm transition-all">Grid</button>
               <button className="px-6 py-1.5 text-[9px] font-black uppercase tracking-widest text-white/40 hover:text-white transition-all">List</button>
            </div>
          </div>
        </div>
        
        {ativos.length === 0 ? (
          <div className="bg-white/[0.02] border border-white/5 border-dashed rounded-sm text-center py-32 group hover:border-[#c5a059]/30 transition-all shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-[#c5a059]/2 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative z-10">
              <div className="w-24 h-24 bg-white/5 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-8 text-white/10 group-hover:text-[#c5a059] group-hover:scale-110 transition-all duration-700">
                 <Ship size={48} strokeWidth={1} />
              </div>
              <h3 className="text-2xl font-serif font-bold text-white mb-4 uppercase tracking-widest">{t('common.no_assets')}</h3>
              <p className="text-white/30 max-w-sm mx-auto mb-10 text-sm font-light leading-relaxed">
                {t('common.start_adding')}
              </p>
              <button className="bg-transparent border border-[#c5a059] text-[#c5a059] hover:bg-[#c5a059] hover:text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all shadow-xl">
                {t('common.add_asset')}
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            {ativos.map((ativo) => (
              <div 
                key={ativo.id} 
                className="group bg-white/[0.02] border border-white/5 rounded-sm overflow-hidden hover:border-[#c5a059]/40 transition-all duration-700 hover:-translate-y-2 shadow-2xl relative"
              >
                {/* Visual Header */}
                <div className="h-56 bg-[#010c20] relative overflow-hidden">
                   <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-transparent to-transparent z-10"></div>
                   <div className="absolute top-5 left-5 z-20">
                      <span className={`px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.3em] border shadow-2xl ${
                        ativo.classificacao === 'superyacht' ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 
                        ativo.classificacao === 'executive' ? 'bg-white/90 border-white text-[#010c20]' : 
                        'bg-white/10 border-white/20 text-white'
                      }`}>
                        {t(`common.${ativo.classificacao}`)}
                      </span>
                   </div>
                   
                   {/* Abstract background icon */}
                   <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] group-hover:opacity-[0.08] group-hover:scale-125 transition-all duration-1000">
                      <Ship size={200} strokeWidth={0.5} />
                   </div>

                   <div className="absolute bottom-6 left-8 z-20">
                      <h3 className="text-2xl font-serif font-bold text-white tracking-tight group-hover:text-[#c5a059] transition-all">
                        {ativo.marca} {ativo.modelo}
                      </h3>
                      <p className="text-[10px] text-white/30 uppercase tracking-[0.4em] font-black mt-2">
                        {ativo.ano_fabricacao} <span className="mx-2 text-[#c5a059]">•</span> {ativo.tipo}
                      </p>
                   </div>
                </div>
                
                {/* Details */}
                <div className="p-8 pt-4">
                  <div className="mb-8">
                    <div className="flex justify-between items-end mb-3">
                      <span className="text-[10px] uppercase tracking-[0.3em] font-black text-white/30">{t('common.progress')}</span>
                      <span className="text-lg font-serif font-bold text-[#c5a059]">{ativo.progresso}%</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden shadow-inner">
                      <div 
                        className="h-full bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(197,160,89,0.3)]"
                        style={{ width: `${ativo.progresso}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                     <div className="flex gap-2">
                        {[1, 2, 3].map(level => (
                          <div 
                            key={level}
                            className={`w-12 h-1 rounded-sm transition-all duration-700 ${
                              ativo.progresso >= (level * 33.3) ? 'bg-[#c5a059]' : 'bg-white/5'
                            }`}
                          />
                        ))}
                     </div>
                     <button className="text-[10px] uppercase tracking-[0.3em] font-black text-white/30 hover:text-[#c5a059] transition-all">
                        {t('common.explore')} →
                     </button>
                  </div>
                </div>

                <div className="px-8 py-5 bg-white/[0.01] border-t border-white/5 flex items-center justify-between text-[9px] uppercase tracking-[0.3em] font-black text-white/20 group-hover:bg-[#c5a059]/5 transition-all">
                   <div className="flex items-center gap-3">
                      {ativo.progresso === 100 ? (
                        <CheckCircle size={16} className="text-[#c5a059]" />
                      ) : (
                        <AlertCircle size={16} className="text-[#c5a059]/40" />
                      )}
                      <span className={ativo.progresso === 100 ? 'text-[#c5a059]' : ''}>
                        {ativo.progresso === 100 ? t('common.cert_complete') : t('common.complete_docs')}
                      </span>
                   </div>
                   <span className="opacity-50">ID: #{ativo.id.slice(0, 4)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}