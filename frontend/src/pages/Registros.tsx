import { useState } from 'react'
import {
  Ship, Anchor, Calendar,
  Clock, CheckCircle, AlertTriangle, Plus
} from 'lucide-react'

export default function Registros() {
  const [, setShowForm] = useState(false)

  return (
    <div className="min-h-screen bg-[#010c20] p-4 md:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-white/5">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Anchor size={20} className="text-white/30 hover:text-[#c5a059] cursor-pointer transition-colors" />
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
          <div className="text-3xl font-bold text-white">0</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Registros</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <CheckCircle size={20} className="text-emerald-400" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Concluídos</span>
          </div>
          <div className="text-3xl font-bold text-white">0</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Este Mês</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <AlertTriangle size={20} className="text-amber-400" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Atenção</span>
          </div>
          <div className="text-3xl font-bold text-white">0</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Pendências</div>
        </div>
        <div className="bg-white/[0.02] border border-white/5 p-6 rounded-sm">
          <div className="flex items-center justify-between mb-3">
            <Calendar size={20} className="text-[#c5a059]" />
            <span className="text-[8px] uppercase tracking-widest text-white/30">Próximos</span>
          </div>
          <div className="text-3xl font-bold text-white">0</div>
          <div className="text-[9px] text-white/40 uppercase tracking-widest mt-1">Agendados</div>
        </div>
      </div>

      {/* Empty State */}
      <div className="text-center py-32 bg-white/[0.01] border border-white/5 rounded-sm mt-6">
        <Ship size={64} strokeWidth={0.5} className="mx-auto text-white/5 mb-6" />
        <p className="text-white/20 text-lg font-serif mb-2">Nenhum registro encontrado</p>
        <p className="text-white/30 text-[10px] uppercase tracking-[0.3em] font-black">
          Comece adicionando o primeiro registro de serviço
        </p>
      </div>
    </div>
  )
}
