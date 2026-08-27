import { useState } from 'react'
import { Save, X } from 'lucide-react'

interface RegistroFormProps {
  onClose: () => void
  onSave: (data: { categoria: string; titulo: string; descricao: string }) => void
}

export default function RegistroForm({ onClose, onSave }: RegistroFormProps) {
  const [formData, setFormData] = useState({
    categoria: 'motor_propulsao',
    titulo: '',
    descricao: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      categoria: formData.categoria,
      titulo: formData.titulo,
      descricao: formData.descricao
    })
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
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
              name="categoria"
              value={formData.categoria}
              onChange={handleChange}
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all"
            >
              <option value="motor_propulsao">Motor e Propulsão</option>
              <option value="manutencao_mecanica">Manutenção Mecânica</option>
              <option value="eletrica_eletronica">Elétrica e Eletrônica</option>
              <option value="seguranca_salvatagem">Segurança e Salvatagem</option>
              <option value="integridade_estrutural">Integridade Estrutural</option>
              <option value="pintura_acabamento">Pintura e Acabamento</option>
              <option value="interior_acomodacoes">Interior e Acomodações</option>
              <option value="documentacao_legal">Documentação Legal</option>
              <option value="navegabilidade">Navegabilidade</option>
            </select>
          </div>

          {/* Título */}
          <div>
            <label className="block text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-3">
              Título do Serviço
            </label>
            <input
              type="text"
              name="titulo"
              value={formData.titulo}
              onChange={handleChange}
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
              name="descricao"
              value={formData.descricao}
              onChange={handleChange}
              placeholder="Descreva o serviço realizado, peças trocadas, observações do técnico..."
              rows={6}
              className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-5 py-4 text-white focus:border-[#c5a059] outline-none transition-all placeholder:text-white/10 resize-none"
              required
            />
          </div>

          {/* Havia aqui duas caixas de upload que NAO eram upload: borda tracejada,
              cursor de mao, "clique para adicionar fotos" — e nenhum
              <input type="file"> no componente inteiro. Clicar nao fazia nada, e
              a tela ja estava no ar. Numa tela que promete cofre imutavel, botao
              que nao responde e pior que botao ausente.

              Ligar de verdade exigiria subir arquivo antes de o registro existir
              (o hash e por documento, nao por registro). Enquanto isso, a tela
              diz a verdade e aponta onde o upload funciona. */}
          <div className="border border-white/10 rounded-sm p-6 bg-white/[0.02]">
            <p className="text-white/50 text-sm leading-relaxed">
              <strong className="text-white/70">Fotos e recibos</strong> deste serviço entram pela
              ficha do ativo, em <strong className="text-white/70">Documentação</strong> — é lá que
              cada arquivo recebe hash e data, e passa a valer no dossiê.
            </p>
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
