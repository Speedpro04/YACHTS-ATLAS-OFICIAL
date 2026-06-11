import { useState, useRef } from 'react'
import { Camera, UploadCloud, CheckCircle2, Shield, AlertCircle, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'

interface SecureCameraUploadProps {
  ativoId: string
  onUploadSuccess: (hash: string) => void
  onClose: () => void
}

export default function SecureCameraUpload({ ativoId, onUploadSuccess, onClose }: SecureCameraUploadProps) {
  const { } = useTranslation()
  const [isUploading, setIsUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleCaptureClick = () => {
    // Isso forçará a abertura da câmera no celular
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)
      
      // Cria um preview rápido para o usuário ver a foto que acabou de tirar
      const objectUrl = URL.createObjectURL(selectedFile)
      setPreview(objectUrl)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      // O backend calcula o SHA-256 real e armazena no Supabase Storage
      const result = await api.documentos.upload(ativoId, 'Vistoria', 'integridade', formData)
      if (!result?.hash) {
        throw new Error('Upload sem hash de integridade')
      }
      onUploadSuccess(result.hash)

    } catch (err: any) {
      setError(err?.message || 'Falha ao processar o arquivo. Verifique sua conexão e tente novamente.')
      console.error(err)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#010c20]/90 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-[#021a3d] border border-white/10 rounded-sm w-full max-w-md overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/5 bg-[#010c20]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#c5a059]/10 flex items-center justify-center">
              <Shield size={16} className="text-[#c5a059]" />
            </div>
            <div>
              <h3 className="text-white font-serif font-bold text-sm tracking-widest uppercase">Captura de Vistoria</h3>
              <p className="text-[9px] text-white/40 font-black uppercase tracking-[0.2em] mt-0.5">Envio Criptografado</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/30 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-6 flex items-center gap-3 p-4 rounded-sm bg-rose-500/10 border border-rose-500/20">
              <AlertCircle size={16} className="text-rose-400 flex-shrink-0" />
              <p className="text-xs text-rose-300">{error}</p>
            </div>
          )}

          {preview ? (
            <div className="space-y-6">
              <div className="relative rounded-sm overflow-hidden border border-white/10 aspect-[3/4] bg-black">
                <img src={preview} alt="Preview" className="w-full h-full object-cover opacity-90" />
                <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-sm border border-white/10 flex items-center gap-2">
                  <CheckCircle2 size={12} className="text-emerald-400" />
                  <span className="text-[9px] font-black uppercase tracking-widest text-emerald-400">Capturado</span>
                </div>
              </div>
              
              <div className="flex gap-4">
                <button 
                  onClick={() => { setPreview(null); setFile(null); }}
                  disabled={isUploading}
                  className="flex-1 py-4 border border-white/10 text-white/60 hover:text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-sm transition-colors disabled:opacity-50"
                >
                  Tirar Outra
                </button>
                <button 
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="flex-[2] bg-[#c5a059] text-[#010c20] py-4 text-[10px] font-black uppercase tracking-[0.2em] rounded-sm transition-all shadow-xl shadow-[#c5a059]/10 flex items-center justify-center gap-3 disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-[#010c20] border-t-transparent rounded-full animate-spin"></div>
                      Criptografando...
                    </>
                  ) : (
                    <>
                      <UploadCloud size={16} />
                      Salvar no Dossiê
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-8">
              <div className="relative">
                <div className="w-24 h-24 rounded-full bg-[#c5a059]/5 border border-[#c5a059]/20 flex items-center justify-center">
                  <Camera size={32} className="text-[#c5a059]" />
                </div>
                <div className="absolute -bottom-2 -right-2 bg-[#021a3d] p-1 rounded-full">
                  <div className="bg-emerald-500/20 text-emerald-400 p-1.5 rounded-full border border-emerald-500/30">
                    <Shield size={12} />
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium text-white/80">A câmera será aberta automaticamente.</p>
                <p className="text-[10px] text-white/40 uppercase tracking-widest max-w-[250px] mx-auto">
                  A foto não será salva na galeria do celular. Ela vai direto para a blockchain do ativo.
                </p>
              </div>

              {/* Input escondido mágico que aciona a câmera no mobile */}
              <input 
                type="file" 
                accept="image/*" 
                capture="environment" 
                ref={fileInputRef}
                className="hidden"
                onChange={handleFileChange}
              />

              <button 
                onClick={handleCaptureClick}
                className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-white py-5 text-[10px] font-black uppercase tracking-[0.3em] rounded-sm transition-all shadow-xl flex items-center justify-center gap-3"
              >
                <Camera size={16} />
                Abrir Câmera
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
