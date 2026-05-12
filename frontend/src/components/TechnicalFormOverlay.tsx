import React, { useState, useRef } from 'react'
import { 
  X, 
  Save, 
  Plus, 
  FileText, 
  Wrench, 
  Zap, 
  Cpu, 
  Shield, 
  Paintbrush, 
  Armchair, 
  FileCheck,
  Calendar,
  User,
  Camera,
  AlertCircle,
  Loader2
} from 'lucide-react'

import { supabase } from '../services/api'

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
  documentacao: 'Documentação & Legal',
  manutencao: 'Registro de Manutenção',
  motor: 'Motor & Propulsão',
  eletrica: 'Sistemas Elétricos & Eletrônicos',
  seguranca: 'Segurança & Salvatagem',
  pintura: 'Pintura & Estética',
  interior: 'Interior & Acabamento',
  dossie: 'Dossiê de Integridade',
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
      const fileName = `${ativoId}-${Date.now()}.${fileExt}`
      const filePath = `${category}/${fileName}`

      const { error: uploadError } = await supabase.storage
        .from('dossier_assets')
        .upload(filePath, file)

      if (uploadError) throw uploadError

      const { data } = supabase.storage
        .from('dossier_assets')
        .getPublicUrl(filePath)

      setUploadedFiles(prev => [...prev, { name: file.name, url: data.publicUrl }])
      setFormData((prev: any) => ({ ...prev, arquivos: [...(prev.arquivos || []), data.publicUrl] }))

    } catch (err: any) {
      console.error('Upload error:', err)
      alert('Erro no upload: ' + err.message)
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
        // seguranca, eletrica, pintura, interior, documentacao
        const { error } = await supabase.from('vessel_inspections').insert({
          ativo_id: ativoId,
          category: category,
          description: formData.descricao || formData.pintura_descricao || formData.interior_descricao,
          observation_alert: formData.observacao,
          items_json: formData // Store checkboxes and other raw data here
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

  const renderFormContent = () => {
    switch (category) {
      case 'motor':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Fabricante</label>
                <div className="relative">
                  <input 
                    type="text" 
                    placeholder="Ex: MTU, Volvo Penta, MAN"
                    className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                    onChange={(e) => setFormData({...formData, fabricante: e.target.value})}
                  />
                  <Zap className="absolute right-4 top-1/2 -translate-y-1/2 text-white/10" size={18} />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Modelo</label>
                <input 
                  type="text" 
                  placeholder="Ex: 16V 2000 M96L"
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                  onChange={(e) => setFormData({...formData, modelo: e.target.value})}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Potência (HP)</label>
                <input 
                  type="number" 
                  placeholder="2600"
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                  onChange={(e) => setFormData({...formData, hp: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Horas</label>
                <input 
                  type="number" 
                  placeholder="120"
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                  onChange={(e) => setFormData({...formData, horas: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Série</label>
                <input 
                  type="text" 
                  placeholder="SN12345"
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                  onChange={(e) => setFormData({...formData, serie: e.target.value})}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Descrição Geral dos Motores</label>
                <textarea 
                  placeholder="Histórico, performance e estado geral..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[80px] resize-none"
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Pontos críticos que exigem atenção imediata..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>
          </div>
        )


      case 'manutencao':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Data do Serviço</label>
                <div className="relative">
                  <input 
                    type="date" 
                    className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                    onChange={(e) => setFormData({...formData, data: e.target.value})}
                  />
                  <Calendar className="absolute right-4 top-1/2 -translate-y-1/2 text-white/10" size={18} />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Responsável Técnico</label>
                <div className="relative">
                  <input 
                    type="text" 
                    placeholder="Nome do Engenheiro ou Oficina"
                    className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none"
                    onChange={(e) => setFormData({...formData, responsavel: e.target.value})}
                  />
                  <User className="absolute right-4 top-1/2 -translate-y-1/2 text-white/10" size={18} />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Descrição do Serviço</label>
                <textarea 
                  placeholder="Descreva detalhadamente o serviço realizado..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[100px] resize-none"
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Ex: Próxima revisão deve focar nos bicos injetores..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>

            <div onClick={triggerFileInput} className="p-8 border-2 border-dashed border-white/5 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/30 transition-colors cursor-pointer group">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-white/20 group-hover:text-[#c5a059] group-hover:bg-[#c5a059]/10 transition-all">
                {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Camera size={24} />}
              </div>
              <div className="text-center">
                <p className="text-white text-xs font-bold">{isUploading ? 'Enviando...' : 'Anexar Nota Fiscal ou Relatório'}</p>
                <p className="text-[9px] text-white/20 uppercase tracking-widest mt-1">
                  {uploadedFiles.length > 0 ? `${uploadedFiles.length} ARQUIVO(S) ANEXADO(S)` : 'PDF, JPG ou PNG até 10MB'}
                </p>
              </div>
            </div>
          </div>
        )

      case 'documentacao':
        return (
          <div className="space-y-8">
            <p className="text-xs text-white/40 leading-relaxed">Faça o upload dos documentos obrigatórios para manter a conformidade do ativo. Arquivos criptografados via <span className="text-[#c5a059]">Atlas Protocol</span>.</p>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Descrição da Situação Documental</label>
                <textarea 
                  placeholder="Informações sobre a validade ou origem dos documentos..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[80px] resize-none"
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção
                </label>
                <textarea 
                  placeholder="Ex: TIE vencendo em 30 dias ou transferência pendente..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>

            <div className="space-y-4">
              {[
                { name: 'Título de Inscrição (TIE)', status: 'pending' },
                { name: 'Seguro DPEM / Apólice', status: 'pending' },
                { name: 'Certificado de Segurança (CSE)', status: 'pending' },
                { name: 'Habilitação do Proprietário', status: 'pending' }
              ].map((doc, i) => (
                <div key={i} className="bg-[#010c20]/30 border border-white/5 p-5 rounded-sm flex items-center justify-between group hover:border-[#c5a059]/20 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-sm bg-white/5 flex items-center justify-center text-white/20 group-hover:text-[#c5a059] transition-colors">
                      <FileText size={20} />
                    </div>
                    <div>
                      <p className="text-sm text-white font-medium">{doc.name}</p>
                      <p className="text-[9px] text-white/20 uppercase tracking-widest mt-1">Status: Aguardando Upload</p>
                    </div>
                  </div>
                  <button onClick={triggerFileInput} type="button" className="px-4 py-2 bg-white/5 hover:bg-[#c5a059] hover:text-[#010c20] text-white/40 text-[9px] font-black uppercase tracking-widest rounded-sm transition-all flex items-center gap-2">
                    {isUploading ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
                    Upload
                  </button>
                </div>
              ))}
            </div>

            <div onClick={triggerFileInput} className="p-8 border-2 border-dashed border-white/5 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/30 transition-colors cursor-pointer group bg-white/[0.01]">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-white/20 group-hover:text-[#c5a059] group-hover:bg-[#c5a059]/10 transition-all">
                {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Plus size={24} />}
              </div>
              <div className="text-center">
                <p className="text-white text-xs font-bold">{isUploading ? 'Enviando...' : 'Adicionar Outro Documento'}</p>
                <p className="text-[9px] text-white/20 uppercase tracking-widest mt-1">
                  {uploadedFiles.length > 0 ? `${uploadedFiles.length} ARQUIVO(S) ADICIONAL(IS)` : 'Notas fiscais, recibos, etc.'}
                </p>
              </div>
            </div>
          </div>
        )

      case 'seguranca':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                'Extintores de Incêndio (Validade)',
                'Coletes Salva-vidas (Quantidade)',
                'Boias Circulares',
                'Pirotécnicos (Foguetes)',
                'Balsa de Abandono',
                'Rádio VHF / EPIRB',
                'Bombas de Esgoto',
                'Ancoragem (Ferro e Amarras)'
              ].map((item, i) => (
                <label key={i} className="bg-[#010c20]/30 border border-white/5 p-4 rounded-sm flex items-center gap-4 cursor-pointer hover:border-[#c5a059]/20 transition-all group">
                  <input type="checkbox" className="w-4 h-4 rounded-sm border-white/10 bg-transparent checked:bg-[#c5a059] focus:ring-0 accent-[#c5a059]" />
                  <span className="text-xs text-white/60 group-hover:text-white transition-colors">{item}</span>
                </label>
              ))}
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Descrição Geral de Segurança</label>
                <textarea 
                  placeholder="Estado geral dos equipamentos de salvatagem..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[80px] resize-none"
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Ex: Requer substituição da bateria do rádio..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>
          </div>
        )

      case 'eletrica':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                'Baterias (Tensão/Carga)',
                'Inversor / Carregador',
                'Painéis Solares (Se houver)',
                'Iluminação de Navegação',
                'Chartplotter / GPS',
                'Sonar / Echo Sounder',
                'Radar',
                'Piloto Automático'
              ].map((item, i) => (
                <label key={i} className="bg-[#010c20]/30 border border-white/5 p-4 rounded-sm flex items-center gap-4 cursor-pointer hover:border-[#c5a059]/20 transition-all group">
                  <input type="checkbox" className="w-4 h-4 rounded-sm border-white/10 bg-transparent checked:bg-[#c5a059] focus:ring-0 accent-[#c5a059]" />
                  <span className="text-xs text-white/60 group-hover:text-white transition-colors">{item}</span>
                </label>
              ))}
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Descrição do Sistema Elétrico</label>
                <textarea 
                  placeholder="Descreva modificações, upgrades ou problemas elétricos..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[80px] resize-none"
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Ex: Inversor apresentando aquecimento ocasional..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>

            <div onClick={triggerFileInput} className="p-8 border-2 border-dashed border-white/5 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/30 transition-colors cursor-pointer group bg-white/[0.01]">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-white/20 group-hover:text-[#c5a059] group-hover:bg-[#c5a059]/10 transition-all">
                {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Camera size={24} />}
              </div>
              <div className="text-center">
                <p className="text-white text-xs font-bold">{isUploading ? 'Enviando...' : 'Upload de Diagramas ou Fotos do Painel'}</p>
                <p className="text-[9px] text-white/20 uppercase tracking-widest mt-1">
                  {uploadedFiles.length > 0 ? `${uploadedFiles.length} ANEXO(S)` : 'Esquemas elétricos e fotos da casa de baterias'}
                </p>
              </div>
            </div>
          </div>
        )

      case 'pintura':
        return (
          <div className="space-y-8">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Estado da Pintura e Gelcoat</label>
                <textarea 
                  placeholder="Descreva o estado atual do costado, convés e pintura de fundo..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[100px] resize-none"
                  onChange={(e) => setFormData({...formData, pintura_descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Ex: Pequena lasca no gelcoat próximo à linha d'água na popa..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Último Polimento</label>
                <input type="date" className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white outline-none" />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Antivegetativa</label>
                <input type="date" className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white outline-none" />
              </div>
            </div>

            <div onClick={triggerFileInput} className="p-8 border-2 border-dashed border-white/5 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/30 transition-colors cursor-pointer group bg-white/[0.01]">
              {isUploading ? <Loader2 size={24} className="animate-spin text-[#c5a059]" /> : <Camera size={24} className="text-white/20 group-hover:text-[#c5a059]" />}
              <div className="text-center">
                <p className="text-white text-xs font-bold">{isUploading ? 'Enviando...' : 'Upload de Fotos do Exterior'}</p>
                {uploadedFiles.length > 0 && <p className="text-[9px] text-[#c5a059] uppercase tracking-widest mt-1">{uploadedFiles.length} ANEXO(S)</p>}
              </div>
            </div>
          </div>
        )

      case 'interior':
        return (
          <div className="space-y-8">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40 ml-1">Condição do Interior e Acabamentos</label>
                <textarea 
                  placeholder="Descreva o estado das tapeçarias, madeiras, eletrônicos e cabines..."
                  className="w-full bg-[#010c20]/50 border border-white/10 rounded-sm py-4 px-5 text-white placeholder:text-white/10 focus:border-[#c5a059]/50 transition-all outline-none min-h-[100px] resize-none"
                  onChange={(e) => setFormData({...formData, interior_descricao: e.target.value})}
                ></textarea>
              </div>
              <div className="space-y-2 p-4 bg-amber-500/5 border border-amber-500/10 rounded-sm">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-500 ml-1 flex items-center gap-2">
                  <AlertCircle size={12} /> Observações de Atenção (Detalhes de Atenção)
                </label>
                <textarea 
                  placeholder="Ex: Estofado do flybridge com pequena mancha..."
                  className="w-full bg-transparent border-none py-2 text-white outline-none min-h-[60px] resize-none placeholder:text-amber-500/20"
                  onChange={(e) => setFormData({...formData, observacao: e.target.value})}
                ></textarea>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {['Ar Condicionado', 'Cozinha', 'Geladeiras', 'Gerador', 'Estofados', 'Madeiras'].map((item, i) => (
                <label key={i} className="bg-[#010c20]/30 border border-white/5 p-4 rounded-sm flex items-center gap-4 cursor-pointer hover:border-[#c5a059]/20 transition-all group">
                  <input type="checkbox" className="accent-[#c5a059]" />
                  <span className="text-[10px] text-white/60 group-hover:text-white transition-colors">{item}</span>
                </label>
              ))}
            </div>

            <div onClick={triggerFileInput} className="p-8 border-2 border-dashed border-white/5 rounded-sm flex flex-col items-center justify-center gap-4 hover:border-[#c5a059]/30 transition-colors cursor-pointer group bg-white/[0.01]">
              {isUploading ? <Loader2 size={24} className="animate-spin text-[#c5a059]" /> : <Camera size={24} className="text-white/20 group-hover:text-[#c5a059]" />}
              <div className="text-center">
                <p className="text-white text-xs font-bold">{isUploading ? 'Enviando...' : 'Upload de Fotos do Interior'}</p>
                {uploadedFiles.length > 0 && <p className="text-[9px] text-[#c5a059] uppercase tracking-widest mt-1">{uploadedFiles.length} ANEXO(S)</p>}
              </div>
            </div>
          </div>
        )


      default:
        return (
          <div className="py-20 flex flex-col items-center justify-center text-white/20">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
              <Icon size={32} strokeWidth={1} />
            </div>
            <p className="font-serif italic text-white/60">Módulo em desenvolvimento</p>
            <p className="text-[10px] uppercase tracking-[0.3em] mt-2">Esta tela será rica em detalhes técnicos para <span className="text-[#c5a059]">{title}</span>.</p>
          </div>
        )
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-[#010c20]/95 backdrop-blur-md animate-in fade-in duration-500" 
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-3xl bg-[#021a3d] border border-white/10 rounded-sm shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-500">
        
        {/* Header */}
        <div className="p-8 border-b border-white/5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-6">
            <div className="w-14 h-14 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059]">
              <Icon size={28} strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="text-white font-serif font-bold text-2xl tracking-tight">{title}</h3>
              <p className="text-[10px] text-white/30 uppercase tracking-[0.3em] mt-1">
                Ativo: <span className="text-white/60">{ativoName}</span> • ID: #{ativoId.slice(0,8).toUpperCase()}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="w-10 h-10 rounded-full border border-white/5 flex items-center justify-center text-white/20 hover:text-white hover:border-white/20 transition-all"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-10 custom-scrollbar">
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileUpload} 
            accept="image/*,.pdf"
          />
          {renderFormContent()}
        </form>

        {/* Footer */}
        <div className="p-8 border-t border-white/5 bg-white/[0.02] flex items-center justify-between shrink-0">
          <button 
            type="button"
            onClick={onClose}
            className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 hover:text-white transition-colors"
          >
            Cancelar
          </button>
          
          <button 
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="group relative px-10 py-4 bg-[#c5a059] hover:bg-[#d4b36d] text-[#010c20] font-black text-[10px] uppercase tracking-[0.3em] rounded-sm transition-all shadow-xl shadow-[#c5a059]/10 disabled:opacity-50 flex items-center gap-3"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-[#010c20]/20 border-t-[#010c20] rounded-full animate-spin"></div>
                Salvando...
              </>
            ) : (
              <>
                <Save size={16} />
                Confirmar Registro
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
