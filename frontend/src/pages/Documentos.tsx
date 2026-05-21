import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo, Documento } from '../types'
import { FileText, Upload, Shield, Download, CheckCircle, Search, FileCheck } from 'lucide-react'

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
      await api.documentos.upload(selectedAtivo, 'documento', 'registro', formData)
      loadDocumentos(selectedAtivo)
    } catch (err) {
      console.error('Erro ao fazer upload:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleDownload = async (docId: string) => {
    try {
      const res = await api.documentos.download(docId)
      if (res && res.url) {
        window.open(res.url, '_blank')
      } else {
        alert('Falha ao obter URL de download do documento.')
      }
    } catch (err) {
      console.error('Erro ao baixar documento:', err)
      alert('Erro ao tentar baixar o documento.')
    }
  }
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4"></div>
        <span className="text-white/40 uppercase tracking-[0.2em] text-xs font-bold">Accessing Vault...</span>
      </div>
    )
  }
  
  return (
    <div className="space-y-10 animate-in fade-in duration-700 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight uppercase flex items-center gap-3">
             <FileCheck size={24} className="text-[#c5a059]" />
             Digital Vault
          </h1>
          <p className="text-white/40 text-sm mt-1 uppercase tracking-widest font-medium">Secured document dossier for your maritime assets</p>
        </div>
        
        <div className="bg-[#0a1326] border border-white/5 p-2 rounded-sm flex items-center gap-4">
           <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold ml-4">Selected Vessel:</span>
           <select
             value={selectedAtivo}
             onChange={(e) => setSelectedAtivo(e.target.value)}
             className="bg-white/5 border border-white/10 rounded-sm px-4 py-2 text-xs text-white focus:border-[#c5a059] outline-none"
           >
             {ativos.map((ativo) => (
               <option key={ativo.id} value={ativo.id} className="bg-[#0a1326]">
                 {ativo.marca} {ativo.modelo}
               </option>
             ))}
           </select>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Left: Upload & Info */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-[#0a1326] border border-white/5 p-8 rounded-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#c5a059]/5 blur-3xl rounded-full group-hover:bg-[#c5a059]/10 transition-all"></div>
            
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-bold text-white uppercase tracking-widest">New Deposit</h3>
              <Shield size={18} className="text-[#c5a059]" />
            </div>

            <label className="block border border-dashed border-white/10 rounded-sm p-10 text-center cursor-pointer hover:border-[#c5a059]/50 transition-all bg-white/[0.02]">
              <input
                type="file"
                onChange={handleUpload}
                disabled={uploading || !selectedAtivo}
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png"
              />
              {uploading ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4"></div>
                  <span className="text-[10px] font-bold text-[#c5a059] uppercase tracking-widest">Encrypting...</span>
                </div>
              ) : (
                <>
                  <Upload size={32} className="mx-auto text-white/10 group-hover:text-[#c5a059] transition-all mb-4" />
                  <p className="text-white text-xs font-bold uppercase tracking-widest mb-1 group-hover:text-[#c5a059] transition-all">Upload Document</p>
                  <p className="text-white/20 text-[10px] uppercase tracking-widest">PDF, JPG, PNG up to 10MB</p>
                </>
              )}
            </label>

            <div className="mt-8 pt-8 border-t border-white/5 space-y-4">
               <div className="flex items-center gap-3 text-white/40">
                  <CheckCircle size={14} className="text-[#c5a059]" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">SHA-256 Immutability</span>
               </div>
               <div className="flex items-center gap-3 text-white/40">
                  <CheckCircle size={14} className="text-[#c5a059]" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">WORM Storage Locking</span>
               </div>
            </div>
          </div>

          <div className="bg-[#c5a059]/5 border border-[#c5a059]/10 p-8 rounded-sm">
             <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059] mb-4">Vault Integrity</h4>
             <p className="text-white/60 text-xs leading-relaxed italic">
               "All documents deposited in the Yachts Atlas vault are automatically hashed and locked. 
               This ensures a tamper-proof digital history for your world-class assets."
             </p>
          </div>
        </div>

        {/* Right: Document List */}
        <div className="lg:col-span-2">
          <div className="bg-[#0a1326] border border-white/5 rounded-sm overflow-hidden flex flex-col min-h-[500px]">
             <div className="p-6 border-b border-white/5 bg-white/2 flex items-center justify-between">
                <h3 className="text-sm font-bold text-white uppercase tracking-widest">Dossier Contents</h3>
                <div className="relative">
                   <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
                   <input 
                     type="text" 
                     placeholder="Search files..." 
                     className="bg-white/5 border border-white/10 rounded-sm pl-9 pr-4 py-1.5 text-[10px] text-white focus:border-[#c5a059]/50 outline-none w-48 transition-all"
                   />
                </div>
             </div>

             <div className="flex-1">
                {documentos.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full py-24">
                    <FileText size={48} className="text-white/5 mb-6" />
                    <p className="text-white/20 uppercase tracking-[0.2em] text-xs font-bold">Vault is currently empty</p>
                  </div>
                ) : (
                  <div className="divide-y divide-white/5">
                    {documentos.map((doc) => (
                      <div key={doc.id} className="group flex items-center justify-between p-6 hover:bg-white/[0.02] transition-all">
                        <div className="flex items-center gap-5">
                          <div className="w-12 h-12 bg-[#050b18] border border-white/5 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:border-[#c5a059]/50 transition-all">
                            <FileText size={20} strokeWidth={1.5} />
                          </div>
                          <div>
                            <p className="text-white font-bold text-sm tracking-tight group-hover:text-[#c5a059] transition-all">{doc.nome_arquivo}</p>
                            <p className="text-[10px] text-white/30 uppercase tracking-[0.2em] mt-1 font-medium">
                              {doc.tipo} • {(doc.tamanho_bytes / 1024).toFixed(1)} KB • {new Date(doc.uploaded_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <span className={`px-3 py-1 rounded-sm text-[8px] font-black uppercase tracking-[0.2em] border shadow-sm ${
                            doc.status === 'verified' ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-[#c5a059]/10 border-[#c5a059]/30 text-[#c5a059]'
                          }`}>
                            {doc.status === 'verified' ? 'Verified' : 'Processing'}
                          </span>
                           <button 
                            onClick={() => handleDownload(doc.id)}
                            className="text-white/20 hover:text-[#c5a059] transition-all p-2 bg-white/5 rounded-full"
                           >
                            <Download size={18} />
                           </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
             </div>

             {documentos.length > 0 && (
                <div className="p-6 border-t border-white/5 bg-[#050b18]/50">
                   <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                         <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                         <span className="text-[9px] font-bold text-white/40 uppercase tracking-widest">All documents cryptographically verified</span>
                      </div>
                      <span className="text-[9px] font-mono text-white/20 uppercase tracking-tighter">
                         Active Hash: {documentos[0]?.hash_sha256?.substring(0, 16)}...
                      </span>
                   </div>
                </div>
             )}
          </div>
        </div>
      </div>
    </div>
  )
}