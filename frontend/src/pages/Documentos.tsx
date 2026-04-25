import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo, Documento } from '../types'
import { FileText, Upload, Shield, Download } from 'lucide-react'

export default function Documentos() {
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [selectedAtivo, setSelectedAtivo] = useState<string>('')
  const [documentos, setDocumentos] = useState<Documento[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  
  useEffect(() => {
    loadAtivos()
  }, [])
  
  useEffect(() => {
    if (selectedAtivo) {
      loadDocumentos(selectedAtivo)
    }
  }, [selectedAtivo])
  
  const loadAtivos = async () => {
    try {
      const data = await api.ativos.list()
      setAtivos(data)
      if (data.length > 0) {
        setSelectedAtivo(data[0].id)
      }
    } catch (err) {
      console.error('Erro:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const loadDocumentos = async (ativoId: string) => {
    try {
      const data = await api.documentos.list(ativoId)
      setDocumentos(data)
    } catch (err) {
      console.error('Erro:', err)
    }
  }
  
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !selectedAtivo) return
    
    const file = e.target.files[0]
    setUploading(true)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('ativo_id', selectedAtivo)
    formData.append('tipo', 'documento')
    formData.append('categoria', 'registro')
    
    try {
      await api.documentos.upload(formData)
      loadDocumentos(selectedAtivo)
    } catch (err) {
      console.error('Erro ao fazer upload:', err)
    } finally {
      setUploading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full"></div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6 pb-20 md:pb-0">
      <div>
        <h1 className="text-2xl font-bold text-white">Documentos</h1>
        <p className="text-gray-400">Upload e verificação de documentos</p>
      </div>
      
      <div className="card">
        <label className="block text-sm text-gray-400 mb-2">Selecione o Ativo</label>
        <select
          value={selectedAtivo}
          onChange={(e) => setSelectedAtivo(e.target.value)}
          className="input w-full md:w-64"
        >
          {ativos.map((ativo) => (
            <option key={ativo.id} value={ativo.id}>
              {ativo.marca} {ativo.modelo}
            </option>
          ))}
        </select>
      </div>
      
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Upload de Documento</h3>
          <div className="flex items-center gap-2 text-sm text-gold-500">
            <Shield size={16} />
            <span>WORM Storage Ativado</span>
          </div>
        </div>
        
        <label className="block border-2 border-dashed border-navy-800 rounded-xl p-8 text-center cursor-pointer hover:border-gold-500 transition-all">
          <input
            type="file"
            onChange={handleUpload}
            disabled={uploading || !selectedAtivo}
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png"
          />
          {uploading ? (
            <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto"></div>
          ) : (
            <>
              <Upload size={32} className="mx-auto text-gray-500 mb-2" />
              <p className="text-white mb-1">Arraste ou clique para upload</p>
              <p className="text-gray-500 text-sm">PDF, JPG, PNG até 10MB</p>
            </>
          )}
        </label>
      </div>
      
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Documentos do Ativo</h3>
        
        {documentos.length === 0 ? (
          <div className="text-center py-12">
            <FileText size={48} className="mx-auto text-gray-500 mb-4" />
            <p className="text-gray-400">Nenhum documento enviado</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documentos.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-4 bg-navy-900 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-navy-800 rounded-lg flex items-center justify-center">
                    <FileText size={20} className="text-gold-500" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{doc.nome_arquivo}</p>
                    <p className="text-gray-500 text-sm">
                      {doc.tipo} • {(doc.tamanho_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    doc.status === 'verified' ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'
                  }`}>
                    {doc.status === 'verified' ? 'Verificado' : 'Pendente'}
                  </span>
                  <button className="p-2 text-gray-400 hover:text-white transition-all">
                    <Download size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="card bg-navy-900/50">
        <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <Shield size={18} className="text-gold-500" />
          Integridade dos Documentos
        </h3>
        <p className="text-gray-400 text-sm">
          Todos os documentos são armazenados com hash SHA-256 e WORM Lock. 
          É impossível alterar ou deletar qualquer arquivo após o upload.
        </p>
        <div className="mt-4 p-4 bg-navy-800 rounded-lg font-mono text-xs text-gray-400">
          <p>Hash: {documentos[0]?.hash_sha256?.substring(0, 32) || '---'}...</p>
        </div>
      </div>
    </div>
  )
}