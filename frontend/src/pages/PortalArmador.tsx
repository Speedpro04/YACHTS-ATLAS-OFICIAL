import { useState, useEffect } from 'react'
import { Ship, Download, Camera, Shield, FileCheck, ArrowRight, Anchor, CheckCircle2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import AssetHealthDashboard from '../components/AssetHealthDashboard'
import SecureCameraUpload from '../components/SecureCameraUpload'

export default function PortalArmador() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [showCamera, setShowCamera] = useState(false)
  
  // Mock data for the owner's vessel
  const ativo = {
    id: 'ya-1029',
    marca: 'Azimut',
    modelo: 'Flybridge 60',
    ano_fabricacao: 2024,
    comprimento_pes: 60,
    porte_categoria: 'executive' as const,
    progresso: 85,
    health: {
      documentacao: 'ok',
      manutencao: 'ok',
      motor: 'ok',
      eletrica: 'ok',
      seguranca: 'warning',
      pintura: 'ok',
      interior: 'ok',
      dossie: 'ok'
    } as any
  }

  useEffect(() => {
    // Simulating loading state
    setTimeout(() => setLoading(false), 1000)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#010c20] flex flex-col items-center justify-center">
        <div className="animate-spin w-12 h-12 border-2 border-[#c5a059] border-t-transparent rounded-full mb-6"></div>
        <span className="text-white/40 uppercase tracking-[0.3em] text-[10px] font-black">Acessando Cofre...</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#010c20] font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20] animate-in fade-in duration-1000">
      
      {/* Premium Header */}
      <div className="border-b border-white/5 bg-[#021a3d]/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <img src="/logo-transparent.png" alt="Yachts Atlas" className="h-8" />
            <div className="hidden md:flex items-center gap-3 pl-6 border-l border-white/10">
              <Shield size={16} className="text-[#c5a059]" />
              <span className="text-[9px] font-black uppercase tracking-[0.3em] text-white/40">Portal do Proprietário</span>
            </div>
          </div>
          <button 
            onClick={() => navigate('/acesso-armador')}
            className="text-[10px] font-black uppercase tracking-widest text-white/30 hover:text-white transition-colors"
          >
            Sair do Cofre
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Welcome Section */}
        <div className="mb-16">
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-4">
            Seu Ativo. <span className="italic text-[#c5a059]">Seu Controle.</span>
          </h1>
          <p className="text-white/40 text-lg font-light max-w-2xl">
            Bem-vindo ao seu cofre digital restrito. Abaixo você tem o painel de integridade exclusivo da sua embarcação.
          </p>
        </div>

        {/* Vessel Banner */}
        <div className="relative rounded-sm overflow-hidden border border-white/10 aspect-[21/9] md:aspect-[21/6] mb-12 group">
          <img 
            src="/ai-generated-boat-picture.jpg"
            alt="Embarcação" 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-1000"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-[#010c20]/50 to-transparent"></div>
          
          <div className="absolute bottom-8 left-8 right-8 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-[10px] font-black text-[#c5a059] border border-[#c5a059]/30 bg-[#c5a059]/10 px-3 py-1 rounded-sm uppercase tracking-widest">
                  {ativo.porte_categoria}
                </span>
                <span className="flex items-center gap-1.5 text-[10px] font-black text-emerald-400 uppercase tracking-widest">
                  <CheckCircle2 size={12} />
                  Ativo Certificado
                </span>
              </div>
              <h2 className="text-3xl font-serif font-bold text-white tracking-tight">{ativo.marca} {ativo.modelo}</h2>
              <div className="flex items-center gap-4 mt-2 text-[10px] text-white/50 uppercase tracking-widest font-black">
                <span>{ativo.comprimento_pes} Pés</span>
                <span className="w-1 h-1 rounded-full bg-white/20"></span>
                <span>Ano {ativo.ano_fabricacao}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4 bg-white/5 backdrop-blur-md border border-white/10 p-4 rounded-sm">
               <Anchor size={24} className="text-[#c5a059]" />
               <div>
                 <p className="text-[8px] uppercase tracking-widest text-white/40 font-black">Identificação Blockchain</p>
                 <p className="text-xs font-mono text-white/80 mt-1">YA-{ativo.id.split('-')[1]}-2024</p>
               </div>
            </div>
          </div>
        </div>

        {/* THE 3 RESTRICTED ITEMS */}
        <div className="grid lg:grid-cols-3 gap-10">
          
          {/* ITEM 1: Asset Health (Takes 2 columns) */}
          <div className="lg:col-span-2 space-y-6">
             <div className="flex items-center justify-between">
                <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
                   <Shield size={20} className="text-[#c5a059]" />
                   1. Integridade do Ativo
                </h3>
             </div>
             
             {/* Componente que já fizemos (responsivo) */}
             <div className="bg-white/[0.02] border border-white/5 rounded-sm p-2 sm:p-6 shadow-2xl">
               <AssetHealthDashboard 
                  mode="operational"
                  healthData={ativo.health}
                  onCategoryClick={(cat) => console.log('Ver detalhes:', cat)}
               />
             </div>
          </div>

          {/* RIGHT COLUMN: Items 2 and 3 */}
          <div className="space-y-10">
            
            {/* ITEM 2: Dossiers & Docs */}
            <div className="space-y-6">
              <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
                 <FileCheck size={20} className="text-[#c5a059]" />
                 2. Dossiês Oficiais
              </h3>
              
              <div className="bg-white/[0.02] border border-white/5 rounded-sm p-6 flex flex-col gap-4">
                <div className="flex items-start gap-4 pb-6 border-b border-white/5">
                  <div className="w-10 h-10 rounded-sm bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white mb-1">Dossiê Válido (SHA-256)</p>
                    <p className="text-[10px] text-white/40 uppercase tracking-widest leading-relaxed">Última atualização: Hoje. Emitido pela Marina Gestora.</p>
                  </div>
                </div>
                
                <button 
                  className="w-full bg-[#c5a059] text-[#010c20] py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 shadow-xl hover:bg-[#b38f4d] transition-all"
                >
                  <Download size={16} />
                  Baixar Dossiê Atual
                </button>
                
                <button 
                  onClick={() => navigate(`/app/pagamento-dossie?ativo_id=${ativo.id}&nivel=${ativo.porte_categoria}`)}
                  className="w-full bg-transparent border border-white/10 text-white/60 hover:text-white py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-colors"
                >
                  Emitir Novo Dossiê (Venda)
                </button>
              </div>
            </div>

            {/* ITEM 3: Camera / Vistoria */}
            <div className="space-y-6">
              <h3 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
                 <Camera size={20} className="text-[#c5a059]" />
                 3. Atualizar Status
              </h3>
              
              <div 
                className="rounded-sm p-8 flex flex-col items-center text-center relative overflow-hidden group border border-[#c5a059]/20 cursor-pointer"
                onClick={() => setShowCamera(true)}
                style={{ background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 100%)' }}
              >
                <div className="absolute inset-0 bg-[#c5a059]/5 group-hover:bg-[#c5a059]/10 transition-colors"></div>
                
                <div className="w-16 h-16 rounded-full bg-[#c5a059]/10 border border-[#c5a059]/30 flex items-center justify-center mb-6 relative z-10 group-hover:scale-110 transition-transform">
                  <Camera size={28} className="text-[#c5a059]" />
                </div>
                
                <h4 className="text-sm font-bold text-white mb-2 relative z-10">Tirar Foto do Ativo</h4>
                <p className="text-[10px] text-white/50 uppercase tracking-widest max-w-[200px] mb-6 relative z-10">
                  A foto será criptografada e enviada diretamente para o Dossiê Blockchain.
                </p>
                
                <div className="flex items-center gap-2 text-[#c5a059] text-[10px] font-black uppercase tracking-widest relative z-10">
                  Abrir Câmera <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
            
          </div>
        </div>
      </div>

      {showCamera && (
        <SecureCameraUpload 
          ativoId={ativo.id}
          onClose={() => setShowCamera(false)}
          onUploadSuccess={(hash) => {
            alert(`Sucesso! Foto encriptada e enviada com segurança.\nSeu patrimônio foi atualizado.\n\nTrilha SHA-256:\n${hash}`)
            setShowCamera(false)
          }}
        />
      )}
    </div>
  )
}
