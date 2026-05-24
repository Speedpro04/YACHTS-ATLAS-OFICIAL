import React, { useState, useRef } from 'react'
import { 
  X, Save, Plus, FileText, Wrench, Zap, Cpu, Shield, Paintbrush, Armchair, FileCheck,
  Calendar, User, Camera, AlertCircle, Loader2
} from 'lucide-react'

import { supabase, api } from '../services/api'

interface TechnicalFormOverlayProps {
  category: string
  ativoId: string
  ativoName: string
  onClose: () => void
  onSave: (data: any) => void
}

const categoryIcons: Record<string, any> = {
  documentacao: FileText,
  manutencao: Wrench,
  motor: Zap,
  eletrica: Cpu,
  seguranca: Shield,
  pintura: Paintbrush,
  interior: Armchair,
  dossie: FileCheck,
}

const categoryTitles: Record<string, string> = {
  documentacao: 'Documentação Legal',
  manutencao: 'Registro de Manutenção',
  motor: 'Motor e Propulsão',
  eletrica: 'Elétrica e Eletrônica',
  seguranca: 'Segurança e Salvatagem',
  pintura: 'Pintura e Acabamento',
  interior: 'Interior e Acomodações',
  dossie: 'Dossiê de Integridade',
}

const checklists: Record<string, string[]> = {
  documentacao: [
    'Título de propriedade (TRAV)', 'Registro de embarcação (REB)', 'Licença de tráfego (LT)',
    'Vistorias da Marinha (histórico)', 'Apólice de seguro vigente', 'Histórico de transferências',
    'Certidão de ônus / gravames', 'Nota fiscal de compra original', 'Manual do fabricante',
    'Certificado de homologação', 'Habilitação do armador', 'DPEM — salvatagem',
    'Despacho de navegação', 'Certidão negativa de débitos', 'Licença ambiental'
  ],
  motor: [
    'Troca de óleo do motor (data/hora)', 'Troca de filtro de óleo', 'Troca de filtro de combustível',
    'Troca de filtro de ar', 'Revisão do impelidor', 'Troca de correia / corrente',
    'Limpeza / troca dos injetores', 'Condição do eixo e hélice', 'Troca de zinco do eixo',
    'Revisão do gearbox / redução', 'Laudo de compressão', 'Horímetro na revisão'
  ],
  eletrica: [
    'Radar (revisão/calibração)', 'VHF fixo e portátil (Anatel)', 'GPS / plotter (mapas)',
    'EPIRB / radiobaliza (bateria)', 'AIS transponder (ativo/passivo)', 'Piloto automático (calibração)',
    'Banco de baterias (idade/carga)', 'Painel solar/gerador/inversor', 'Sistema de bilge automática',
    'Fiação (última inspeção)', 'Instrumentação de navegação', 'Sistema de entretenimento'
  ],
  seguranca: [
    'Coletes salva-vidas (validade)', 'Boia de salvamento em arco', 'Extintor de incêndio (carga)',
    'Sinalizadores pirotécnicos', 'Bomba manual de esgotamento', 'Âncora + cadeia (condição)',
    'Cordame e cabos de atracação', 'Kit de primeiros socorros', 'Detector de CO (monóxido)',
    'Sinalização noturna (lanternas)', 'Plano de emergência', 'Buzina / sino de nevoeiro'
  ],
  pintura: [
    'Aplicação de antiincrustante', 'Tipo e marca da tinta utilizada', 'Número de demãos aplicadas',
    'Pintura acima da linha d\'água', 'Polimento / enceramento (gelcoat)', 'Tratamento de teca (deck)',
    'Reparos de gelcoat (trincas)'
  ],
  interior: [
    'Estofados e forração', 'Sistema de ar condicionado', 'Fogão, forno e gás',
    'Sistema de esgoto / macerador', 'Bomba de água doce (pressurização)', 'Aquecedor de água (boiler)',
    'Móveis e marcenaria interna', 'Cabines (condição geral)', 'Banheiros / camarotes',
    'Iluminação interna (LED)'
  ]
}

export default function TechnicalFormOverlay({ category, ativoId, ativoName, onClose, onSave }: TechnicalFormOverlayProps) {
  const Icon = categoryIcons[category] || FileText
  const title = categoryTitles[category] || 'Formulário Técnico'
  
  const [formData, setFormData] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<{name: string, url: string}[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const fileExt = file.name.split('.').pop()
      const fileName = `${ativoId}/${category}/${Date.now()}.${fileExt}`
      
      const { error: uploadError, data } = await supabase.storage
        .from('media')
        .upload(fileName, file, { upsert: false })

      if (uploadError) throw uploadError

      const { data: { publicUrl } } = supabase.storage
        .from('media')
        .getPublicUrl(fileName)

      if (publicUrl) {
        setUploadedFiles(prev => [...prev, { name: file.name, url: publicUrl }])
        setFormData((prev: any) => ({ ...prev, arquivos: [...(prev.arquivos || []), publicUrl] }))
      } else {
        throw new Error('Falha ao obter URL pública do documento.')
      }

    } catch (err: any) {
      console.error('Upload error:', err)
      alert('Erro no upload: ' + (err.message || err))
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (category === 'motor') {
        const { error } = await supabase.from('engines').insert({
          ativo_id: ativoId,
          fabricante: formData.fabricante,
          modelo: formData.modelo,
          hp: parseInt(formData.hp) || null,
          horas: parseInt(formData.horas) || null,
          serie: formData.serie,
          description: formData.descricao,
          observation_alert: formData.observacao
        })
        if (error) throw error
      } else if (category === 'manutencao') {
        const { error } = await supabase.from('maintenance_logs').insert({
          ativo_id: ativoId,
          description: formData.descricao,
          data: formData.data,
          responsavel: formData.responsavel,
          observation_alert: formData.observacao
        })
        if (error) throw error
      } else {
        const { error } = await supabase.from('vessel_inspections').insert({
          ativo_id: ativoId,
          category: category,
          description: formData.descricao || formData.pintura_descricao || formData.interior_descricao,
          observation_alert: formData.observacao,
          items_json: formData
        })
        if (error) throw error
      }

      onSave({ category, ...formData })
      onClose()
    } catch (err: any) {
      console.error('Error saving technical data:', err)
      alert('Erro ao salvar os dados: ' + err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCheck = (item: string) => {
    setFormData((prev: any) => {
      const current = prev.checkedItems || []
      const isChecked = current.includes(item)
      return {
        ...prev,
        checkedItems: isChecked ? current.filter((i: string) => i !== item) : [...current, item]
      }
    })
  }

  // Estilos de Input High Ticket
  const inputStyle = "w-full bg-white border border-gray-200 rounded-sm py-4 px-5 text-gray-800 font-medium placeholder:text-gray-400 focus:border-[#c5a059] focus:ring-1 focus:ring-[#c5a059] transition-all outline-none text-sm shadow-inner"
  const labelStyle = "text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] ml-1 mb-2 block"

  const renderChecklist = (items: string[]) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-8">
      {items.map((item, i) => {
        const isChecked = (formData.checkedItems || []).includes(item)
        return (
          <div 
            key={i} 
            onClick={() => handleCheck(item)}
            className={`flex items-center gap-4 p-4 rounded-sm border cursor-pointer transition-all duration-300 ${
              isChecked 
                ? 'bg-[#c5a059]/10 border-[#c5a059]/50 shadow-[0_0_15px_rgba(197,160,89,0.1)]' 
                : 'bg-[#010c20]/50 border-white/5 hover:border-[#c5a059]/30'
            }`}
          >
            <div className={`w-5 h-5 rounded-sm flex items-center justify-center border transition-colors ${
              isChecked ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 'bg-[#010c20] border-white/20 text-transparent'
            }`}>
              <Save size={12} strokeWidth={3} className={isChecked ? 'opacity-100' : 'opacity-0'} />
            </div>
            <span className={`text-[11px] font-semibold tracking-wide uppercase transition-colors ${
              isChecked ? 'text-[#c5a059]' : 'text-white/60'
            }`}>
              {item}
            </span>
          </div>
        )
      })}
    </div>
  )

  const renderFormContent = () => {
    switch (category) {
      case 'motor':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className={labelStyle}>Fabricante</label>
                <div className="relative">
                  <input type="text" placeholder="Ex: MTU, Volvo Penta, MAN" className={inputStyle} onChange={(e) => setFormData({...formData, fabricante: e.target.value})} />
                  <Zap className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                </div>
              </div>
              <div>
                <label className={labelStyle}>Modelo</label>
                <input type="text" placeholder="Ex: 16V 2000 M96L" className={inputStyle} onChange={(e) => setFormData({...formData, modelo: e.target.value})} />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className={labelStyle}>Potência (HP)</label>
                <input type="number" placeholder="2600" className={inputStyle} onChange={(e) => setFormData({...formData, hp: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Horas</label>
                <input type="number" placeholder="120" className={inputStyle} onChange={(e) => setFormData({...formData, horas: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Série</label>
                <input type="text" placeholder="SN12345" className={inputStyle} onChange={(e) => setFormData({...formData, serie: e.target.value})} />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className={labelStyle}>Descrição Geral dos Motores</label>
                <textarea placeholder="Histórico, performance e estado geral..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, descricao: e.target.value})}></textarea>
              </div>
              <div className="p-6 bg-[#021431] border border-[#c5a059]/20 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] ml-1 flex items-center gap-2 mb-3">
                  <AlertCircle size={14} /> Observações de Atenção
                </label>
                <textarea placeholder="Pontos críticos que exigem atenção imediata..." className={`${inputStyle} bg-white text-gray-800 min-h-[80px] resize-none`} onChange={(e) => setFormData({...formData, observacao: e.target.value})}></textarea>
              </div>
            </div>

            <div className="pt-6 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Checklist de Propulsão</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Itens obrigatórios de inspeção</p>
              {renderChecklist(checklists.motor)}
            </div>
          </div>
        )

      case 'manutencao':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className={labelStyle}>Data do Serviço</label>
                <div className="relative">
                  <input type="date" className={inputStyle} onChange={(e) => setFormData({...formData, data: e.target.value})} />
                </div>
              </div>
              <div>
                <label className={labelStyle}>Responsável Técnico</label>
                <div className="relative">
                  <input type="text" placeholder="Nome do Engenheiro ou Oficina" className={inputStyle} onChange={(e) => setFormData({...formData, responsavel: e.target.value})} />
                  <User className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                </div>
              </div>
            </div>

            <div>
              <label className={labelStyle}>Descrição do Serviço</label>
              <textarea placeholder="Descreva detalhadamente o serviço realizado..." className={`${inputStyle} min-h-[120px] resize-none`} onChange={(e) => setFormData({...formData, descricao: e.target.value})}></textarea>
            </div>
            
            <div className="p-6 bg-[#021431] border border-[#c5a059]/20 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] ml-1 flex items-center gap-2 mb-3">
                  <AlertCircle size={14} /> Observações de Atenção
                </label>
                <textarea placeholder="Ex: Próxima revisão focar em compressores..." className={`${inputStyle} bg-white text-gray-800 min-h-[80px] resize-none`} onChange={(e) => setFormData({...formData, observacao: e.target.value})}></textarea>
            </div>

            <div onClick={triggerFileInput} className="p-10 border border-white/10 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/50 transition-colors cursor-pointer group bg-[#010c20]/50 shadow-inner">
              <div className="w-16 h-16 rounded-full bg-[#021a3d] border border-white/5 flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Camera size={24} />}
              </div>
              <div className="text-center">
                <p className="text-[#e5d5b7] font-serif text-lg">{isUploading ? 'Enviando...' : 'Anexar Nota Fiscal ou Laudo'}</p>
                <p className="text-[9px] text-white/30 uppercase tracking-widest mt-2">
                  {uploadedFiles.length > 0 ? <span className="text-[#c5a059] font-bold">{uploadedFiles.length} ARQUIVO(S) ANEXADO(S)</span> : 'PDF, JPG ou PNG até 10MB'}
                </p>
              </div>
            </div>
          </div>
        )

      case 'documentacao':
        return (
          <div className="space-y-8">
            <div>
              <label className={labelStyle}>Situação Documental</label>
              <textarea placeholder="Informações sobre a validade ou origem dos documentos..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, descricao: e.target.value})}></textarea>
            </div>

            <div className="pt-2 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Conformidade Legal</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Marque os documentos conferidos</p>
              {renderChecklist(checklists.documentacao)}
            </div>

            <div onClick={triggerFileInput} className="p-10 border border-white/10 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/50 transition-colors cursor-pointer group bg-[#010c20]/50 shadow-inner mt-8">
              <div className="w-16 h-16 rounded-full bg-[#021a3d] border border-white/5 flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Plus size={24} />}
              </div>
              <div className="text-center">
                <p className="text-[#e5d5b7] font-serif text-lg">{isUploading ? 'Enviando...' : 'Fazer Upload de Documentos'}</p>
                <p className="text-[9px] text-white/30 uppercase tracking-widest mt-2">
                  {uploadedFiles.length > 0 ? <span className="text-[#c5a059] font-bold">{uploadedFiles.length} ANEXO(S)</span> : 'Arraste os arquivos ou clique'}
                </p>
              </div>
            </div>
          </div>
        )

      case 'seguranca':
        return (
          <div className="space-y-8">
            <div>
              <label className={labelStyle}>Relatório de Salvatagem</label>
              <textarea placeholder="Estado geral dos equipamentos de salvatagem e combate a incêndio..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, descricao: e.target.value})}></textarea>
            </div>
            
            <div className="pt-2 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Checklist de Segurança</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Itens vitais de proteção</p>
              {renderChecklist(checklists.seguranca)}
            </div>
          </div>
        )

      case 'eletrica':
        return (
          <div className="space-y-8">
            <div>
              <label className={labelStyle}>Sistemas Elétricos</label>
              <textarea placeholder="Descreva estado das fiações, baterias, plotters e eletrônica..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, descricao: e.target.value})}></textarea>
            </div>
            
            <div className="pt-2 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Inspeção Eletrônica</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Componentes de navegação e energia</p>
              {renderChecklist(checklists.eletrica)}
            </div>
          </div>
        )

      case 'pintura':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className={labelStyle}>Último Polimento</label>
                <input type="date" className={inputStyle} onChange={(e) => setFormData({...formData, polimento_data: e.target.value})} />
              </div>
              <div>
                <label className={labelStyle}>Última Antivegetativa</label>
                <input type="date" className={inputStyle} onChange={(e) => setFormData({...formData, antivegetativa_data: e.target.value})} />
              </div>
            </div>
            
            <div>
              <label className={labelStyle}>Condição da Superfície</label>
              <textarea placeholder="Descreva gelcoat, costado e estado do fundo..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, pintura_descricao: e.target.value})}></textarea>
            </div>
            
            <div className="pt-2 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Itens de Acabamento Externo</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Verificação estética e estrutural de superfície</p>
              {renderChecklist(checklists.pintura)}
            </div>
          </div>
        )

      case 'interior':
        return (
          <div className="space-y-8">
            <div>
              <label className={labelStyle}>Condição do Interior</label>
              <textarea placeholder="Tapeçaria, madeiras, hidraúlica e conforto..." className={`${inputStyle} min-h-[100px] resize-none`} onChange={(e) => setFormData({...formData, interior_descricao: e.target.value})}></textarea>
            </div>
            
            <div className="pt-2 border-t border-white/5">
              <h4 className="text-[#e5d5b7] font-serif font-bold text-lg mb-2">Acomodações e Conforto</h4>
              <p className="text-[10px] uppercase tracking-widest text-white/40">Avaliação do mobiliário e climatização</p>
              {renderChecklist(checklists.interior)}
            </div>
          </div>
        )

      default:
        return (
          <div className="py-20 flex flex-col items-center justify-center text-white/20">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
              <Icon size={32} strokeWidth={1} />
            </div>
            <p className="font-serif italic text-[#e5d5b7] text-lg">Módulo em Desenvolvimento</p>
            <p className="text-[10px] uppercase tracking-[0.3em] mt-2">Esta tela será rica em detalhes técnicos para <span className="text-[#c5a059]">{title}</span>.</p>
          </div>
        )
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10">
      <div className="absolute inset-0 bg-[#010c20]/95 backdrop-blur-md animate-in fade-in duration-500" onClick={onClose} />
      
      <div className="relative w-full max-w-4xl bg-[#021431] border border-[#c5a059]/20 rounded-sm shadow-[0_0_50px_rgba(1,12,32,0.9)] flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-500">
        
        {/* Header */}
        <div className="p-8 md:p-10 border-b border-white/5 flex items-center justify-between shrink-0 bg-[#010c20]/80">
          <div className="flex items-center gap-6">
            <div className="w-14 h-14 bg-[#c5a059]/10 border border-[#c5a059]/30 rounded-sm flex items-center justify-center text-[#c5a059] shadow-[0_0_15px_rgba(197,160,89,0.15)]">
              <Icon size={28} strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="text-[#e5d5b7] font-serif font-bold text-3xl tracking-tight">{title}</h3>
              <p className="text-[10px] text-[#c5a059] uppercase tracking-[0.3em] mt-2 font-black">
                Dossiê Oficial <span className="text-white/20 mx-2">•</span> {ativoName}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="w-12 h-12 rounded-sm border border-white/5 flex items-center justify-center text-white/20 hover:text-[#c5a059] hover:border-[#c5a059]/30 hover:bg-[#c5a059]/5 transition-all">
            <X size={24} strokeWidth={1} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 md:p-10 custom-scrollbar">
          <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept="image/*,.pdf" />
          {renderFormContent()}
        </form>

        {/* Footer */}
        <div className="p-6 md:p-8 border-t border-[#c5a059]/20 bg-[#010c20] flex items-center justify-between shrink-0 shadow-[0_-10px_30px_rgba(1,12,32,0.5)]">
          <button type="button" onClick={onClose} className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 hover:text-[#c5a059] transition-colors">
            Cancelar Operação
          </button>
          
          <button 
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="group relative px-12 py-5 bg-gradient-to-r from-[#c5a059] to-[#b38f4d] hover:from-[#d4b36d] hover:to-[#c5a059] text-[#010c20] font-black text-[11px] uppercase tracking-[0.3em] rounded-sm transition-all shadow-[0_0_25px_rgba(197,160,89,0.2)] hover:shadow-[0_0_35px_rgba(197,160,89,0.4)] hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-4"
          >
            {isSubmitting ? (
              <>
                <div className="w-5 h-5 border-2 border-[#010c20]/20 border-t-[#010c20] rounded-full animate-spin"></div>
                Processando...
              </>
            ) : (
              <>
                <Save size={18} />
                Selar Informações
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
