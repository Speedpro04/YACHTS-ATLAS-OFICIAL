import { useState } from 'react'
import { Ship, Anchor, Calendar, Clock, CheckCircle, AlertTriangle, Plus, Wrench, Shield, Zap, FileText, Camera, Activity, Oil, Box, Ship as ShipIcon } from 'lucide-react'
import RegistroForm from '../components/RegistroForm'

interface Registro {
  id: string
  categoria: string
  titulo: string
  descricao: string
  data: string
  status: 'pending' | 'completed' | 'attention'
}

const CATEGORIAS = {
  motor_propulsao: { label: 'Motor e Propulsão', icon: Oil, color: '#3b82f6' },
  manutencao_mecanica: { label: 'Manutenção Mecânica', icon: Wrench, color: '#f59e0b' },
  eletrica_eletronica: { label: 'Elétrica e Eletrônica', icon: Zap, color: '#8b5cf6' },
  seguranca_salvatagem: { label: 'Segurança e Salvatagem', icon: Shield, color: '#ef4444' },
  integridade_estrutural: { label: 'Integridade Estrutural', icon: Box, color: '#10b981' },
  pintura_acabamento: { label: 'Pintura e Acabamento', icon: Camera, color: '#ec4899' },
  interior_acomodacoes: { label: 'Interior e Acomodações', icon: ShipIcon, color: '#14b8a6' },
  documentacao_legal: { label: 'Documentação Legal', icon: FileText, color: '#c5a059' },
  navegabilidade: { label: 'Navegabilidade', icon: Activity, color: '#f97316' }
}

export default function Registros() {
  const [showForm, setShowForm] = useState(false)
  const [registros, setRegistros] = useState<Registro[]>([])
  const [filtroCategoria, setFiltroCategoria] = useState<string>('todas')

  const registrosFiltrados = filtroCategoria === 'todas'
    ? registros
    : registros.filter(r => r.categoria === filtroCategoria)

  const handleSave = (data: Omit<Registro, 'id' | 'data' | 'status'>) => {
    const newRegistro: Registro = {
      ...data,
      id: Date.now().toString(),
      data: new Date().toISOString(),
      status: 'pending'
    }
    // Registro imutável - uma vez salvo, não muda mais
    setRegistros(prev => [...prev, newRegistro])
    setShowForm(false)
  }

  return (
    <div className="min-h-screen bg-[#010c20] p-4 md:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-white/5">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Anchor size={20} className="text-white/30" />
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-white">Histórico de Serviços</h1>
          </div>
          <p className="text-white/40 text-[10px] uppercase tracking-[0.4em] font-black ml-12">
            Cofre Digital de Registros Imutáveis
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-8 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3 shadow-xl shadow-[#c5a059]/10 self-start"
        >
          <Plus size={16} />
          Novo Registro
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 py-8">
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <Clock size={20} className="text-[#c5a059]" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Total</span>
          </div>
          <div className="text-3xl font-bold text-white">{registros.length}</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Registros</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <CheckCircle size={20} className="text-emerald-400" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Concluídos</span>
          </div>
          <div className="text-3xl font-bold text-white">{registros.filter(r => r.status === 'completed').length}</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Este Mês</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <AlertTriangle size={20} className="text-amber-400" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Atenção</span>
          </div>
          <div className="text-3xl font-bold text-white">{registros.filter(r => r.status === 'attention').length}</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Pendências</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <Calendar size={20} className="text-[#c5a059]" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Próximos</span>
          </div>
          <div className="text-3xl font-bold text-white">{registros.filter(r => r.status === 'pending').length}</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Agendados</div>
        </div>
      </div>

      {/* Categorias Grid */}
      <div className="py-8">
        <h2 className="text-xl font-serif font-bold text-white mb-6">Categorias de Serviços</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Object.entries(CATEGORIAS).map(([key, { label, icon: Icon, color }]) => {
            const count = registros.filter(r => r.categoria === key).length
            return (
              <button
                key={key}
                onClick={() => setFiltroCategoria(filtroCategoria === key ? 'todas' : key)}
                className={`p-4 rounded-sm border transition-all duration-300 ${
                  filtroCategoria === key
                    ? 'border-[#c5a059] bg-[#c5a059]/10'
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <Icon size={20} style={{ color }} />
                  <span className="text-[10px] uppercase tracking-widest text-white/60">
                    {filtroCategoria === key ? 'Filtrado' : 'Filtrar'}
                  </span>
                </div>
                <p className="text-white font-serif text-sm mb-1">{label}</p>
                <p className="text-[24px] font-bold text-[#c5a059]">{count}</p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Registros List */}
      {registros.length > 0 ? (
        <div className="mt-8 space-y-4">
          {registrosFiltrados.map(registro => {
            const CategoriaIcon = CATEGORIAS[registro.categoria as keyof typeof CATEGORIAS]?.icon || FileText
            const categoriaCor = CATEGORIAS[registro.categoria as keyof typeof CATEGORIAS]?.color || '#fff'
            return (
              <div key={registro.id} className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-sm" style={{ backgroundColor: `${categoriaCor}15` }}>
                      <CategoriaIcon size={24} style={{ color: categoriaCor }} />
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className="text-[10px] uppercase tracking-widest px-2 py-1 rounded-sm"
                          style={{ backgroundColor: `${categoriaCor}20`, color: categoriaCor }}
                        >
                          {CATEGORIAS[registro.categoria as keyof typeof CATEGORIAS]?.label}
                        </span>
                        <span className="text-[10px] uppercase tracking-widest text-white/30">
                          {new Date(registro.data).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                      <h3 className="text-lg font-serif font-bold text-white">{registro.titulo}</h3>
                      <p className="text-white/40 text-sm mt-1">{registro.descricao}</p>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        /* Empty State */
        <div className="text-center py-32 bg-white/[0.01] border border-white/5 rounded-sm mt-6">
          <Ship size={64} strokeWidth={0.5} className="mx-auto text-white/5 mb-6" />
          <p className="text-white/20 text-lg font-serif mb-2">Nenhum registro encontrado</p>
          <p className="text-white/30 text-[10px] uppercase tracking-[0.3em] font-black">
            Comece adicionando o primeiro registro de serviço
          </p>
        </div>
      )}

      {showForm && <RegistroForm onClose={() => setShowForm(false)} onSave={handleSave} />}
    </div>
  )
}