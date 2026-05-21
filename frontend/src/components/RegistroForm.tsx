import { Camera, Upload, Save, X } from 'lucide-react'

interface RegistroFormProps {
  onClose: () => void
  onSave: (data: any) => void
}

export default function RegistroForm({ onClose, onSave }: RegistroFormProps) {

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({})
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#010c20] border border-white/10 rounded-sm max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-8 border-b border-white/5 flex items-center justify-between sticky top-0 bg-[#010c20] z-10">
          <div>
            <h2 className="text-2xl font-serif font-bold text-white">Novo Registro de Serviço</h2>
            <p className="text-white/40 text-[10px] uppercase tracking-widest mt-1">Cofre Digital Imutável</p>
          </div>
          <button onClick={onClose} className="text-white/30 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          {/* Categoria */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Categoria do Serviço
            </label>
            <select
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all"
            >
              <option value="motor_propulsao" className="bg-[#010c20]">Motor e Propulsão</option>
              <option value="manutencao_mecanica" className="bg-[#010c20]">Manutenção Mecânica</option>
              <option value="eletrica_eletronica" className="bg-[#010c20]">Elétrica e Eletrônica</option>
              <option value="seguranca_salvatagem" className="bg-[#010c20]">Segurança e Salvatagem</option>
              <option value="integridade_estrutural" className="bg-[#010c20]">Integridade Estrutural</option>
              <option value="pintura_acabamento" className="bg-[#010c20]">Pintura e Acabamento</option>
              <option value="interior_acomodacoes" className="bg-[#010c20]">Interior e Acomodações</option>
              <option value="documentacao_legal" className="bg-[#010c20]">Documentação Legal</option>
              <option value="navegabilidade" className="bg-[#010c20]">Navegabilidade</option>
            </select>
          </div>

          {/* Título */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Título do Serviço
            </label>
            <input
              type="text"
              placeholder="Ex: Troca de óleo - Motor Volvo Penta D6-370"
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all placeholder:text-white/10"
              required
            />
          </div>

          {/* Descrição */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Descrição Detalhada
            </label>
            <textarea
              placeholder="Descreva o serviço realizado, peças trocadas, observações do técnico..."
              rows={6}
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all placeholder:text-white/10 resize-none"
              required
            />
          </div>

          {/* Upload de Fotos */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Fotos do Serviço (Antes/Depois)
            </label>
            <div className="border-2 border-dashed border-white/10 rounded-sm p-8 text-center hover:border-[#c5a059]/50 transition-colors cursor-pointer">
              <Camera className="mx-auto text-white/20 mb-4" size={48} />
              <p className="text-white/40 text-sm mb-2">Clique para adicionar fotos</p>
              <p className="text-white/20 text-[10px] uppercase tracking-widest">JPG, PNG - Máx 10MB</p>
            </div>
          </div>

          {/* Upload de Recibos */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Recibos e Comprovantes
            </label>
            <div className="border-2 border-dashed border-white/10 rounded-sm p-8 text-center hover:border-[#c5a059]/50 transition-colors cursor-pointer">
              <Upload className="mx-auto text-white/20 mb-4" size={48} />
              <p className="text-white/40 text-sm mb-2">Clique para adicionar recibos</p>
              <p className="text-white/20 text-[10px] uppercase tracking-widest">PDF, JPG - Máx 10MB</p>
            </div>
          </div>

          {/* Ações */}
          <div className="flex gap-4 pt-8 border-t border-white/5">
            <button
              type="submit"
              className="flex-1 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 shadow-xl"
            >
              <Save size={18} />
              Salvar Registro (Imutável)
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-8 bg-white/5 hover:bg-white/10 text-white py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
