import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, Trash2, Anchor, Filter, Search, ChevronRight, X, ArrowLeft, Download, ExternalLink, Award, Camera, FileCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import AssetHealthDashboard from '../components/AssetHealthDashboard'
import SecureCameraUpload from '../components/SecureCameraUpload'
import TechnicalFormOverlay from '../components/TechnicalFormOverlay'
import DossieCategorias from '../components/DossieCategorias'

export default function Ativos() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    if (location.state && (location.state as any).openForm) {
      setShowForm(true)
    }
  }, [location.state])
  const [selectedAtivo, setSelectedAtivo] = useState<Ativo | null>(null)
  const [showCamera, setShowCamera] = useState(false)
  const [formData, setFormData] = useState({
    tipo: 'iate',
    marca: '',
    modelo: '',
    comprimento_pes: 0,
    ano_fabricacao: new Date().getFullYear(),
  })
  
  const [editingCategory, setEditingCategory] = useState<string | null>(null)
  
  // Fake Dossier Data for Prototyping
  const mockDossiers: Record<string, any> = {
    '1a2b3c': {
      imo_number: 'IMO 9876543',
      flag: 'Malta',
      hull_material: 'Fibra de Carbono / GRP',
      engines: [
        { manufacturer: 'MTU', model: '16V 2000 M96L', hp: 2600, hours: 120 },
        { manufacturer: 'MTU', model: '16V 2000 M96L', hp: 2600, hours: 121 }
      ],
      last_ultrasound: '20 Mai 2026',
      ultrasound_result: 'Aprovado - Integridade 99.8%',
      inspector: 'Atlas Global Surveyors',
      photo: '/moored-yacht-mediterranean-sea-port-buildings-street-greenery-barcelona-spain.jpg',
      maintenance_history: [
        { date: '15 Mar 2026', service: 'Revisão 100h Motores', status: 'concluido' },
        { date: '02 Jan 2026', service: 'Troca de Estabilizadores Seakeeper', status: 'concluido' }
      ]
    },
    '4d5e6f': {
      imo_number: 'REG 5544332',
      flag: 'Brasil',
      hull_material: 'Fibra de Vidro Reforçada',
      engines: [
        { manufacturer: 'MAN', model: 'V12-1400', hp: 1400, hours: 450 },
        { manufacturer: 'MAN', model: 'V12-1400', hp: 1400, hours: 455 }
      ],
      last_ultrasound: '05 Jan 2026',
      ultrasound_result: 'Aprovado - Requer Pintura Antivegetativa',
      inspector: 'DNV Certified Inspector',
      photo: '/ai-generated-boat-picture.jpg',
      maintenance_history: [
        { date: '10 Fev 2026', service: 'Pintura Antivegetativa (Fundo)', status: 'concluido' },
        { date: '12 Out 2025', service: 'Revisão de Geradores Onan', status: 'concluido' }
      ]
    },
    '7g8h9i': {
      imo_number: 'BR-4433221',
      flag: 'Brasil',
      hull_material: 'GRP',
      engines: [
        { manufacturer: 'Volvo Penta', model: 'D6-440', hp: 440, hours: 85 }
      ],
      last_ultrasound: '12 Abr 2026',
      ultrasound_result: 'Aprovado - Condição Nova',
      inspector: 'Atlas NDT Local',
      photo: '/ai-generated-boat-picture (1).jpg',
      maintenance_history: [
        { date: '20 Abr 2026', service: 'Instalação de Sistema de Som Fusion', status: 'concluido' },
        { date: '15 Jan 2026', service: 'Entrega Técnica e Revisão Zero', status: 'concluido' }
      ]
    }
  }

  // Helper to get current dossier
  const currentDossier = selectedAtivo ? (mockDossiers[selectedAtivo.id] || mockDossiers['1a2b3c']) : null;
  
  useEffect(() => {
    loadAtivos()
  }, [])
  
  const loadAtivos = async () => {
    try {
      const data = await api.ativos.list()
      
      // MOCK DATA: 3 Embarcações (Fake) para Protótipo
      const mockData: Ativo[] = [
        {
          id: '1a2b3c',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u1111111-1111-1111-1111-111111111111',
          proprietario_nome: 'Roberto Marinho Jr.',
          marca: 'Azimut',
          modelo: 'Grande Trideck',
          ano_fabricacao: 2023,
          comprimento_pes: 100,
          tipo: 'iate',
          porte_categoria: 'superyacht',
          classificacao: 'gold',
          progresso: 100,
          status: 'ativo',
          created_at: '2023-01-15T00:00:00Z'
        },
        {
          id: '4d5e6f',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u2222222-2222-2222-2222-222222222222',
          proprietario_nome: 'Dra. Isabella Diniz',
          marca: 'Ferretti',
          modelo: 'Yachts 780',
          ano_fabricacao: 2021,
          comprimento_pes: 79,
          tipo: 'iate',
          porte_categoria: 'executive',
          classificacao: 'silver',
          progresso: 85,
          status: 'ativo',
          created_at: '2021-06-10T00:00:00Z'
        },
        {
          id: '7g8h9i',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u3333333-3333-3333-3333-333333333333',
          proprietario_nome: 'Dr. Fernando Almeida',
          marca: 'Focker',
          modelo: '450 Gran Coupe',
          ano_fabricacao: 2020,
          comprimento_pes: 45,
          tipo: 'lancha',
          porte_categoria: 'compact',
          classificacao: 'bronze',
          progresso: 45,
          status: 'ativo',
          created_at: '2020-03-20T00:00:00Z'
        }
      ]
      
      if (data && data.length > 0) {
        setAtivos(data)
      } else {
        setAtivos(mockData)
      }
      
    } catch (err) {
      console.error('Erro ao carregar ativos:', err)
      // MOCK DATA Fallback
      const mockData: Ativo[] = [
        {
          id: '1a2b3c',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u1111111-1111-1111-1111-111111111111',
          proprietario_nome: 'Roberto Marinho Jr.',
          marca: 'Azimut',
          modelo: 'Grande Trideck',
          ano_fabricacao: 2023,
          comprimento_pes: 100,
          tipo: 'iate',
          porte_categoria: 'superyacht',
          classificacao: 'gold',
          progresso: 100,
          status: 'ativo',
          created_at: '2023-01-15T00:00:00Z'
        },
        {
          id: '4d5e6f',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u2222222-2222-2222-2222-222222222222',
          proprietario_nome: 'Dra. Isabella Diniz',
          marca: 'Ferretti',
          modelo: 'Yachts 780',
          ano_fabricacao: 2021,
          comprimento_pes: 79,
          tipo: 'iate',
          porte_categoria: 'executive',
          classificacao: 'silver',
          progresso: 85,
          status: 'ativo',
          created_at: '2021-06-10T00:00:00Z'
        },
        {
          id: '7g8h9i',
          marina_id: 'm1111111-1111-1111-1111-111111111111',
          owner_id: 'u3333333-3333-3333-3333-333333333333',
          proprietario_nome: 'Dr. Fernando Almeida',
          marca: 'Focker',
          modelo: '450 Gran Coupe',
          ano_fabricacao: 2020,
          comprimento_pes: 45,
          tipo: 'lancha',
          porte_categoria: 'compact',
          classificacao: 'bronze',
          progresso: 45,
          status: 'ativo',
          created_at: '2020-03-20T00:00:00Z'
        }
      ]
      setAtivos(mockData)
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
    if (confirm('Tem certeza que deseja excluir este ativo?')) {
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
                { label: 'Ano de Fabricação', key: 'ano_fabricacao', type: 'number', min: 1900, max: new Date().getFullYear() }
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
              <button type="submit" className="bg-[#c5a059] text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] shadow-xl hover:bg-[#b38f4d] transition-all">Confirmar Cadastro</button>
              <button type="button" onClick={() => setShowForm(false)} className="text-white/30 hover:text-white px-8 py-4 text-[10px] font-black uppercase tracking-[0.3em] transition-all">Cancelar</button>
            </div>
          </form>
        </div>
      )}

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
      
      {/* Tabela de Ativos / Detalhe do Ativo */}
      {!selectedAtivo ? (
        <div className="bg-white/[0.01] border border-white/5 rounded-sm overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-white/[0.01]">
                  <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20">Embarcação</th>
                  <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20 hidden md:table-cell">Especificações</th>
                  <th className="py-6 px-8 text-[10px] uppercase tracking-[0.4em] font-black text-white/20">Categoria</th>
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
                        <div className="text-[10px] text-white/20 uppercase tracking-[0.2em] font-medium">Fabricado em {ativo.ano_fabricacao}</div>
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
                         <button 
                           onClick={() => setSelectedAtivo(ativo)}
                           className="w-10 h-10 flex items-center justify-center border border-white/5 text-white/10 hover:text-[#c5a059] hover:border-[#c5a059]/30 rounded-sm transition-all"
                         >
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
      ) : (
        <div className="animate-in slide-in-from-right-10 duration-700 space-y-10">
           <div className="flex flex-col lg:flex-row gap-10">
              {/* Coluna Esquerda - Foto e Dados */}
              <div className="lg:w-1/3 space-y-6">
                <div className="relative group rounded-sm overflow-hidden border border-white/10 aspect-video">
                  <img 
                    src={currentDossier?.photo || "/boat-picture-light.jpg"}
                    alt="Embarcação" 
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-1000"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] to-transparent"></div>
                  <button 
                    className="absolute top-4 left-4 flex items-center gap-2 bg-[#010c20]/80 backdrop-blur-md border border-white/10 px-4 py-2 rounded-sm text-[9px] font-black uppercase tracking-widest text-white/60 hover:text-[#c5a059] transition-colors" 
                    onClick={() => setSelectedAtivo(null)}
                  >
                    <ArrowLeft size={14} />
                    Voltar à Lista
                  </button>
                </div>
                
                <div className="bg-white/[0.02] border border-white/5 p-8 rounded-sm space-y-6">
                   <div className="flex items-center justify-between">
                      <h2 className="text-2xl font-serif font-bold text-white tracking-tight">{selectedAtivo.marca} {selectedAtivo.modelo}</h2>
                      <span className="text-[10px] font-black text-[#c5a059] border border-[#c5a059]/30 px-3 py-1 rounded-sm uppercase tracking-widest">{selectedAtivo.porte_categoria}</span>
                   </div>
                   
                   <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-1">
                         <span className="block text-[10px] uppercase tracking-widest text-white/40 font-medium">Fabricante</span>
                         <span className="block text-[20px] text-[#F0EDE6] font-semibold">{selectedAtivo.marca}</span>
                      </div>
                      <div className="space-y-1">
                         <span className="block text-[10px] uppercase tracking-widest text-white/40 font-medium">Ano</span>
                         <span className="block text-[20px] text-[#F0EDE6] font-semibold">{selectedAtivo.ano_fabricacao}</span>
                      </div>
                      <div className="space-y-1">
                         <span className="block text-[10px] uppercase tracking-widest text-white/40 font-medium">Comprimento</span>
                         <span className="block text-[20px] text-[#F0EDE6] font-semibold">{selectedAtivo.comprimento_pes} pés</span>
                      </div>
                      <div className="space-y-1">
                         <span className="block text-[10px] uppercase tracking-widest text-white/40 font-medium">Progresso</span>
                         <span className="block text-[20px] text-[#F0EDE6] font-semibold">{selectedAtivo.progresso}%</span>
                      </div>
                   </div>
                   
                   <div className="pt-6 border-t border-white/5 flex flex-col gap-3">
                      <button 
                        onClick={() => setShowCamera(true)}
                        className="w-full bg-white/5 border border-white/10 hover:bg-white/10 text-white py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-colors">
                         <Camera size={16} />
                         Registrar Foto de Vistoria
                      </button>
                      <button 
                        onClick={() => navigate(`/app/pagamento-dossie?ativo_id=${selectedAtivo.id}&pes=${selectedAtivo.comprimento_pes}`)}
                        className="w-full bg-[#c5a059] text-[#010c20] py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 shadow-xl hover:bg-[#b38f4d] transition-colors">
                         <Download size={16} />
                         Gerar Dossiê (Serviço Pago)
                      </button>
                      <button className="w-full bg-transparent hover:bg-white/5 text-white/40 hover:text-white/80 py-4 rounded-sm text-[9px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-colors">
                         <ExternalLink size={14} />
                         Compartilhar Acesso de Visualização
                      </button>
                   </div>
                </div>
              </div>
              
              {/* Coluna Direita - Dossiê + Dashboard de Saúde */}
              <div className="lg:w-2/3 space-y-10">
                 {/* Categorias do Dossiê (sob medida por porte do ativo) */}
                 <DossieCategorias
                   ativoId={selectedAtivo.id}
                   ativoNome={`${selectedAtivo.marca} ${selectedAtivo.modelo}`}
                   comprimentoPes={selectedAtivo.comprimento_pes}
                 />

                 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <h3 className="text-xl font-serif font-bold text-white tracking-tight uppercase flex items-center gap-4">
                       <Award size={24} className="text-[#c5a059]" />
                       Dashboard de Integridade do Ativo
                    </h3>
                    <div className="flex items-center gap-6">
                       <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                          <span className="text-[8px] font-black text-white/20 uppercase tracking-widest">Operacional</span>
                       </div>
                       <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                          <span className="text-[8px] font-black text-white/20 uppercase tracking-widest">Atenção</span>
                       </div>
                       <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-rose-500"></div>
                          <span className="text-[8px] font-black text-white/20 uppercase tracking-widest">Crítico</span>
                       </div>
                    </div>
                 </div>
                 
                 <AssetHealthDashboard 
                    healthData={selectedAtivo.health_status || {
                      documentacao: 'ok',
                      manutencao: 'warning',
                      motor: 'ok',
                      eletrica: 'ok',
                      seguranca: 'critical',
                      pintura: 'ok',
                      interior: 'ok',
                      dossie: 'na'
                    }}
                    onCategoryClick={(cat) => setEditingCategory(cat)}
                 />
                 
                 {/* Relatório Básico do Dossiê */}
                 <div className="bg-[#021a3d]/50 border border-white/10 p-8 rounded-sm shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-[#c5a059]/5 blur-[50px] rounded-full pointer-events-none"></div>
                    
                    <div className="flex items-center justify-between mb-8 relative z-10">
                       <h4 className="text-sm font-serif font-bold tracking-tight text-white flex items-center gap-3">
                         <FileCheck size={18} className="text-[#c5a059]" />
                         Relatório Básico (Extrato do Dossiê)
                       </h4>
                       <span className="text-[9px] font-black uppercase tracking-[0.3em] text-[#c5a059] border border-[#c5a059]/30 px-3 py-1 rounded-sm bg-[#c5a059]/10">Imutável</span>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 relative z-10">
                       {/* Identidade */}
                       <div className="space-y-4">
                         <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 border-b border-white/5 pb-2">Identidade Técnica</h5>
                         <div className="space-y-3">
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Registro IMO</span>
                             <span className="text-xs text-[#F0EDE6] font-medium">{currentDossier?.imo_number}</span>
                           </div>
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Bandeira</span>
                             <span className="text-xs text-[#F0EDE6] font-medium">{currentDossier?.flag}</span>
                           </div>
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Material do Casco</span>
                             <span className="text-xs text-[#F0EDE6] font-medium">{currentDossier?.hull_material}</span>
                           </div>
                         </div>
                       </div>

                       {/* Inspeção END */}
                       <div className="space-y-4">
                         <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#c5a059] border-b border-[#c5a059]/20 pb-2 flex items-center gap-2">
                           <Search size={12} />
                           Laudo Ultrassom (END)
                         </h5>
                         <div className="space-y-3">
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Última Análise</span>
                             <span className="text-xs text-[#F0EDE6] font-medium">{currentDossier?.last_ultrasound}</span>
                           </div>
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Diagnóstico</span>
                             <span className="text-xs text-emerald-400 font-medium">{currentDossier?.ultrasound_result}</span>
                           </div>
                           <div className="flex justify-between">
                             <span className="text-xs text-white/50">Inspetor</span>
                             <span className="text-xs text-[#F0EDE6] font-medium">{currentDossier?.inspector}</span>
                           </div>
                         </div>
                       </div>
                       
                       {/* Motorização */}
                       <div className="col-span-1 md:col-span-2 space-y-4 pt-4 border-t border-white/5">
                         <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 pb-2">Motorização Principal</h5>
                         <div className="grid grid-cols-2 gap-4">
                           {currentDossier?.engines.map((engine: any, idx: number) => (
                             <div key={idx} className="bg-white/5 p-4 rounded-sm border border-white/5 flex justify-between items-center">
                               <div>
                                 <span className="block text-[10px] text-white/40 uppercase tracking-widest mb-1">Motor {idx + 1}</span>
                                 <span className="block text-sm text-[#F0EDE6] font-semibold">{engine.manufacturer} {engine.model}</span>
                               </div>
                               <div className="text-right">
                                 <span className="block text-xs text-[#c5a059] font-bold">{engine.hp} HP</span>
                                 <span className="block text-[10px] text-white/40 mt-1">{engine.hours} horas</span>
                               </div>
                             </div>
                           ))}
                         </div>
                       </div>
                    </div>
                 </div>
                 
                 {/* Log de Auditoria */}
                 <div className="bg-white/[0.02] border border-white/5 p-8 rounded-sm">
                    <div className="flex items-center justify-between mb-8">
                       <h4 className="text-xs font-black uppercase tracking-[0.3em] text-white/40">Registro de Atividades Críticas</h4>
                       <button className="text-[9px] font-black uppercase tracking-widest text-[#c5a059]">Ver Histórico Completo</button>
                    </div>
                    
                    <div className="space-y-6">
                       {[
                         { date: '12 Mai 2026', action: 'Revisão de Motor Concluída', user: 'Técnico da Marina', type: 'maintenance' },
                         { date: '05 Mai 2026', action: 'Atualização de Documento: Renovação do Seguro', user: 'Administrador', type: 'doc' },
                         { date: '28 Abr 2026', action: 'Inspeção de Equipamentos de Segurança Reprovada', user: 'Vistoriador', type: 'critical' }
                       ].map((log, idx) => (
                         <div key={idx} className="flex items-center justify-between py-4 border-b border-white/5 last:border-0">
                            <div className="flex items-center gap-4">
                               <div className={`w-2 h-2 rounded-full flex-shrink-0 ${log.type === 'critical' ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]' : 'bg-[#c5a059]/40'}`}></div>
                               <div>
                                  <p className="text-sm text-white font-medium">{log.action}</p>
                                  <p className="text-[9px] text-white/20 uppercase tracking-widest mt-1">{log.user} • {log.date}</p>
                               </div>
                            </div>
                            <ChevronRight size={14} className="text-white/10 flex-shrink-0" />
                         </div>
                       ))}
                    </div>
                 </div>
              </div>
           </div>
        </div>
      )}

      {showCamera && selectedAtivo && (
        <SecureCameraUpload 
          ativoId={selectedAtivo.id}
          onClose={() => setShowCamera(false)}
          onUploadSuccess={(hash) => {
            alert(`Sucesso! Foto criptografada e enviada.\nHash SHA-256:\n${hash}`)
            setShowCamera(false)
          }}
        />
      )}

      {editingCategory && selectedAtivo && (
        <TechnicalFormOverlay 
          category={editingCategory}
          ativoId={selectedAtivo.id}
          ativoName={`${selectedAtivo.marca} ${selectedAtivo.modelo}`}
          onClose={() => setEditingCategory(null)}
          onSave={(data) => {
            console.log('Dados salvos:', data)
            // Aqui futuramente chamaremos a API do Supabase
            alert(`Registro de ${editingCategory} salvo com sucesso!`)
            setEditingCategory(null)
          }}
        />
      )}
    </div>
  )
}
