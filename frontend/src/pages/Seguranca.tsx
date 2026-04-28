import { useTranslation } from 'react-i18next'
import { ShieldCheck, Lock, Database, FileCheck, Cpu, Key, Fingerprint, Search, Shield } from 'lucide-react'
import Header from '../components/Header'
import { Link } from 'react-router-dom'

export default function Seguranca() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter']">
      <Header />

      <main className="mt-[180px]">
        {/* Hero Section */}
        <section className="relative py-32 overflow-hidden border-b border-white/5">
          <div className="absolute inset-0 opacity-20">
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-[#c5a059]/5 blur-[180px] rounded-full pointer-events-none"></div>
          </div>

          <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8">
               <ShieldCheck size={14} className="text-[#c5a059]" />
               <span className="text-[10px] font-bold text-white uppercase tracking-widest">Protocolo de Integridade Universal</span>
            </div>
            <h1 className="text-5xl md:text-8xl font-serif font-bold text-white mb-10 tracking-tight leading-[0.9]">
              Segurança em <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">Criptografia Pura.</span>
            </h1>
            <p className="text-xl text-white/50 max-w-2xl mx-auto leading-relaxed font-light">
              Protegemos o seu legado através de uma infraestrutura de dados imutável. No Yachts Atlas, a verdade sobre o seu ativo é gravada matematicamente.
            </p>
          </div>
        </section>

        {/* Core Pillars */}
        <section className="py-32">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid md:grid-cols-3 gap-12">
              {[
                { 
                  icon: Database, 
                  title: 'Imutabilidade WORM', 
                  desc: 'Write Once, Read Many. Uma vez que um dado de manutenção ou documento é validado, ele se torna permanente. Alterações retroativas são impossíveis.' 
                },
                { 
                  icon: Fingerprint, 
                  title: 'Hashing SHA-256', 
                  desc: 'Cada registro possui uma assinatura digital única. Qualquer tentativa de fraude é detectada instantaneamente pelo protocolo de integridade.' 
                },
                { 
                  icon: Lock, 
                  title: 'Criptografia de Nível Bancário', 
                  desc: 'Seus documentos e dados sensíveis são armazenados em silos criptográficos isolados, acessíveis apenas via chaves de segurança exclusivas.' 
                }
              ].map((pillar, i) => (
                <div key={i} className="group p-10 bg-white/[0.02] border border-white/5 rounded-sm hover:border-[#c5a059]/40 transition-all duration-700">
                   <div className="w-16 h-16 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] mb-8 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                      <pillar.icon size={28} />
                   </div>
                   <h3 className="text-2xl font-serif font-bold text-white mb-4 tracking-tight group-hover:text-[#c5a059] transition-all">{pillar.title}</h3>
                   <p className="text-white/40 leading-relaxed text-sm font-light">{pillar.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Technical Deep Dive */}
        <section className="py-40 bg-[#021431]/30 border-y border-white/5 relative overflow-hidden">
           <div className="max-w-7xl mx-auto px-6 relative z-10">
              <div className="grid lg:grid-cols-2 gap-24 items-center">
                 <div>
                    <h2 className="text-4xl md:text-5xl font-serif font-bold text-white mb-8 tracking-tight">O DNA do seu Ativo, Blindado.</h2>
                    <p className="text-white/40 text-lg leading-relaxed mb-12 font-light">
                      Nossa arquitetura foi desenhada para atender aos padrões mais rigorosos de auditoria internacional. Não somos apenas um software de gestão; somos uma camada de confiança para o mercado marítimo global.
                    </p>
                    
                    <div className="space-y-8">
                       {[
                         { icon: Cpu, title: 'Processamento em Tempo Real', desc: 'Monitoramento contínuo de status e conformidade.' },
                         { icon: FileCheck, title: 'Auditoria Automatizada', desc: 'Verificação cruzada de documentos e históricos técnicos.' },
                         { icon: Search, title: 'Rastreabilidade Total', desc: 'Cadeia de custódia inquebrável desde o primeiro registro.' }
                       ].map((item, i) => (
                         <div key={i} className="flex gap-6 items-start">
                            <div className="mt-1 text-[#c5a059]">
                               <item.icon size={20} />
                            </div>
                            <div>
                               <h4 className="text-white font-bold uppercase tracking-widest text-[10px] mb-2">{item.title}</h4>
                               <p className="text-white/30 text-sm leading-relaxed">{item.desc}</p>
                            </div>
                         </div>
                       ))}
                    </div>
                 </div>

                 <div className="relative">
                    <div className="aspect-square bg-gradient-to-tr from-[#c5a059]/20 to-transparent rounded-full flex items-center justify-center border border-[#c5a059]/10 p-12">
                       <div className="w-full h-full border border-[#c5a059]/20 rounded-full flex items-center justify-center animate-pulse">
                          <div className="w-2/3 h-2/3 border border-[#c5a059]/40 rounded-full flex items-center justify-center shadow-[0_0_100px_rgba(197,160,89,0.1)]">
                             <Shield size={120} strokeWidth={0.5} className="text-[#c5a059]" />
                          </div>
                       </div>
                    </div>
                    {/* Decorative elements */}
                    <div className="absolute top-0 right-0 w-32 h-px bg-[#c5a059]/40"></div>
                    <div className="absolute bottom-0 left-0 w-32 h-px bg-[#c5a059]/40"></div>
                 </div>
              </div>
           </div>
        </section>

        {/* Security Vault Section */}
        <section className="py-40">
           <div className="max-w-4xl mx-auto px-6 text-center">
              <Key size={64} strokeWidth={0.5} className="mx-auto text-[#c5a059] mb-12" />
              <h2 className="text-5xl font-serif font-bold text-white mb-8 tracking-tight">O Cofre Atlas.</h2>
              <p className="text-white/40 text-xl leading-relaxed mb-16 font-light">
                Cada proprietário recebe uma chave de acesso criptográfica única. Somente você e as entidades autorizadas (marinas, seguradoras) podem visualizar o dossiê completo. Sua privacidade é o nosso protocolo padrão.
              </p>
              <Link to="/login" className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-16 py-6 rounded-sm text-[10px] font-black uppercase tracking-[0.4em] transition-all shadow-2xl inline-block">
                Acessar meu Cofre
              </Link>
           </div>
        </section>
      </main>

      <footer className="py-20 border-t border-white/5 text-center">
         <p className="text-[10px] text-white/20 uppercase tracking-[0.5em]">Yachts Atlas • Cryptographic Integrity • Global Trust</p>
      </footer>
    </div>
  )
}
