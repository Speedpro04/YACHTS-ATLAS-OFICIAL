import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Users, Shield, Briefcase, ExternalLink, Search, Filter, Star } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface Partner {
  id: string
  name: string
  company_name?: string
  type: 'broker' | 'insurance'
  email: string
  phone: string
  website?: string
  logo_url?: string
  rating?: number
  commission_rate?: number
  verified?: boolean
}

export default function Parceiros() {
  const { t } = useTranslation()
  const [partners, setPartners] = useState<Partner[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'broker' | 'insurance'>('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadPartners()
  }, [])

  const loadPartners = async () => {
    // Simulating API call for now since we just created the backend endpoints
    // In a real scenario, we would call api.partners.list()
    const mockPartners: Partner[] = [
      {
        id: '1',
        name: 'Oceanic Brokers',
        company_name: 'Oceanic Brokers Ltd',
        type: 'broker',
        email: 'contact@oceanic.com',
        phone: '+55 11 99999-9999',
        website: 'https://oceanic.com',
        rating: 4.9,
        verified: true
      },
      {
        id: '2',
        name: 'Allianz Nautical',
        company_name: 'Allianz Insurance Group',
        type: 'insurance',
        email: 'nautical@allianz.com',
        phone: '+55 11 88888-8888',
        website: 'https://allianz.com',
        rating: 4.8,
        verified: true
      },
      {
        id: '3',
        name: 'Vanguard Yacht Sales',
        company_name: 'Vanguard Global',
        type: 'broker',
        email: 'sales@vanguard.com',
        phone: '+55 21 77777-7777',
        rating: 4.7,
        verified: false
      }
    ]
    
    setPartners(mockPartners)
    setLoading(false)
  }

  const filteredPartners = partners.filter(p => {
    const matchesType = filter === 'all' || p.type === filter
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                          (p.company_name?.toLowerCase().includes(search.toLowerCase()))
    return matchesType && matchesSearch
  })

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 border-b border-white/5 pb-12">
        <div>
          <h1 className="text-5xl font-serif font-bold text-white mb-4 tracking-tight">
            {t('common.partners')}
          </h1>
          <p className="text-white/40 uppercase tracking-[0.3em] text-[10px] font-black">
            {t('common.find_partners')}
          </p>
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
            <input 
              type="text" 
              placeholder="Buscar parceiros..."
              className="bg-white/5 border border-white/10 rounded-sm pl-12 pr-6 py-4 text-white text-sm focus:outline-none focus:border-[#c5a059]/50 w-full md:w-80 transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex bg-white/5 border border-white/10 rounded-sm p-1">
             <button 
               onClick={() => setFilter('all')}
               className={`px-6 py-2 text-[10px] font-black uppercase tracking-widest rounded-sm transition-all ${filter === 'all' ? 'bg-[#c5a059] text-[#010c20]' : 'text-white/40 hover:text-white'}`}
             >
               Todos
             </button>
             <button 
               onClick={() => setFilter('broker')}
               className={`px-6 py-2 text-[10px] font-black uppercase tracking-widest rounded-sm transition-all ${filter === 'broker' ? 'bg-[#c5a059] text-[#010c20]' : 'text-white/40 hover:text-white'}`}
             >
               Brokers
             </button>
             <button 
               onClick={() => setFilter('insurance')}
               className={`px-6 py-2 text-[10px] font-black uppercase tracking-widest rounded-sm transition-all ${filter === 'insurance' ? 'bg-[#c5a059] text-[#010c20]' : 'text-white/40 hover:text-white'}`}
             >
               Seguros
             </button>
          </div>
        </div>
      </div>

      {/* Partners Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
          {filteredPartners.map((partner) => (
            <div 
              key={partner.id}
              className="group bg-white/[0.02] border border-white/5 rounded-sm p-8 hover:border-[#c5a059]/40 transition-all duration-700 hover:-translate-y-2 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-[#c5a059]/5 blur-[40px] rounded-full translate-x-1/2 -translate-y-1/2"></div>
              
              <div className="flex items-start justify-between mb-8">
                <div className="w-16 h-16 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] group-hover:scale-110 transition-transform duration-500">
                   {partner.type === 'broker' ? <Briefcase size={28} /> : <Shield size={28} />}
                </div>
                <div className="flex items-center gap-1 bg-[#c5a059]/10 px-3 py-1 rounded-full">
                  <Star size={12} className="text-[#c5a059] fill-[#c5a059]" />
                  <span className="text-[10px] font-black text-[#c5a059]">{partner.rating}</span>
                </div>
              </div>

              <h3 className="text-2xl font-serif font-bold text-white mb-2 tracking-tight group-hover:text-[#c5a059] transition-all">
                {partner.name}
              </h3>
              <p className="text-[10px] text-white/30 uppercase tracking-[0.3em] font-black mb-6">
                {partner.type === 'broker' ? 'Broker Autorizado' : 'Seguradora Parceira'}
              </p>

              <div className="space-y-4 mb-8">
                 <div className="flex items-center gap-3 text-white/50 text-sm font-light">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#c5a059]/40"></span>
                    {partner.email}
                 </div>
                 <div className="flex items-center gap-3 text-white/50 text-sm font-light">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#c5a059]/40"></span>
                    {partner.phone}
                 </div>
              </div>

              <div className="flex items-center justify-between pt-8 border-t border-white/5">
                 {partner.verified && (
                   <div className="flex items-center gap-2 text-[#c5a059]">
                      <Shield size={14} />
                      <span className="text-[8px] font-black uppercase tracking-widest">Verificado Atlas</span>
                   </div>
                 )}
                 <button className="text-[10px] font-black uppercase tracking-[0.3em] text-white/30 hover:text-[#c5a059] transition-all flex items-center gap-2">
                    Contatar <ExternalLink size={12} />
                 </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* CTA Partner */}
      <div className="bg-gradient-to-r from-[#021431] to-[#010c20] border border-[#c5a059]/20 p-12 rounded-sm text-center relative overflow-hidden group">
         <div className="absolute inset-0 bg-[#c5a059]/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
         <h3 className="text-3xl font-serif font-bold text-white mb-4 relative z-10">Torne-se um Parceiro Autorizado.</h3>
         <p className="text-white/40 max-w-2xl mx-auto mb-10 text-sm font-light leading-relaxed relative z-10">
           Seja você um broker ou uma seguradora, integre-se ao ecossistema Yachts Atlas e ofereça segurança imutável para seus clientes.
         </p>
         <button className="bg-[#c5a059] text-[#010c20] px-12 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.4em] transition-all relative z-10 hover:scale-105 shadow-2xl">
           Solicitar Credenciamento
         </button>
      </div>
    </div>
  )
}
