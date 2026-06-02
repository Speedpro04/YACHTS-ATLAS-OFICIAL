import { Ship, Anchor, Globe, Users, Star, ArrowRight } from 'lucide-react'
import Header from '../components/Header'
import { Link } from 'react-router-dom'

export default function Frota() {
  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter']">
      <Header />

      <main className="mt-[var(--header-h)]">
        {/* Hero Section */}
        <section className="relative py-[328px] overflow-hidden border-b border-white/5">
          <div className="absolute inset-0">
            <img 
              src="/fleet-hero-light.jpg" 
              alt="Azimut Yacht" 
              className="w-full h-full object-cover"
              loading="lazy"
            />
            {/* Dark Blue Overlay covering the entire boat/image */}
            <div className="absolute inset-0 bg-[#010c20]/[0.92]"></div>
          </div>

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="max-w-3xl">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-12 h-px bg-[#c5a059]"></div>
                <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#c5a059]">Atlas Global Fleet</span>
              </div>
              <h1 className="text-5xl md:text-7xl font-serif font-bold text-white mb-8 tracking-tight leading-tight">
                A Excelência em <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">Movimento.</span>
              </h1>
              <p className="text-lg md:text-xl text-white leading-relaxed font-light max-w-2xl">
                Navegue pela frota mais exclusiva do mundo. Ativos de alto valor protegidos por um protocolo de integridade que garante transparência total e valorização contínua.
              </p>
            </div>
          </div>
        </section>

        {/* Fleet Showcase */}
        <section className="py-32">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid lg:grid-cols-12 gap-16 items-center mb-32">
              <div className="lg:col-span-7">
                 <div className="relative rounded-sm overflow-hidden group shadow-2xl">
                    <img 
                      src="/smala-light.jpg" 
                      alt="Superyacht" 
                      className="w-full h-[500px] object-cover transition-transform duration-1000 group-hover:scale-105 brightness-75"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-transparent to-transparent"></div>
                    <div className="absolute bottom-10 left-10">
                       <span className="bg-[#c5a059] text-[#010c20] px-4 py-1.5 rounded-sm text-[10px] font-black uppercase tracking-widest mb-4 inline-block">Flagship Ativo</span>
                       <h3 className="text-3xl font-serif font-bold text-white tracking-tight">SMALA Superyacht</h3>
                    </div>
                 </div>
              </div>
              <div className="lg:col-span-5 space-y-8">
                 <h2 className="text-4xl font-serif font-bold text-white tracking-tight">O Ápice do Luxo Customizado.</h2>
                 <p className="text-white/40 leading-relaxed text-lg font-light">
                   O SMALA representa o pináculo da frota global. Uma embarcação onde cada sistema, desde a propulsão híbrida até a automação interna, é monitorado em tempo real pelo nosso protocolo de custódia.
                 </p>
                 <div className="grid grid-cols-2 gap-8 pt-8">
                    <div>
                       <p className="text-3xl font-serif font-bold text-[#c5a059]">80ft+</p>
                       <p className="text-[10px] text-white/20 uppercase tracking-[0.2em] font-black mt-2">Categoria Superyacht</p>
                    </div>
                    <div>
                       <p className="text-3xl font-serif font-bold text-[#c5a059]">100%</p>
                       <p className="text-[10px] text-white/20 uppercase tracking-[0.2em] font-black mt-2">Auditoria Digital</p>
                    </div>
                 </div>
              </div>
            </div>

            {/* Stats Bar */}
            <div className="grid md:grid-cols-4 gap-8 py-20 border-y border-white/5 mb-32 bg-white/[0.01]">
               {[
                 { icon: Ship, label: 'Ativos Geridos', value: '450+' },
                 { icon: Globe, label: 'Países Atendidos', value: '12' },
                 { icon: Anchor, label: 'Marinas Parceiras', value: '85' },
                 { icon: Users, label: 'Proprietários UHNW', value: '320' }
               ].map((stat, i) => (
                 <div key={i} className="text-center group">
                    <stat.icon size={32} className="mx-auto text-[#c5a059]/40 mb-6 group-hover:text-[#c5a059] transition-all" strokeWidth={1} />
                    <p className="text-4xl font-serif font-bold text-white mb-2">{stat.value}</p>
                    <p className="text-[9px] text-white/20 uppercase tracking-[0.3em] font-black">{stat.label}</p>
                 </div>
               ))}
            </div>

            {/* Fleet Categories */}
            <div className="text-center mb-20">
               <h2 className="text-4xl font-serif font-bold text-white mb-6">Diversidade e Exclusividade.</h2>
               <p className="text-white/40 max-w-xl mx-auto text-lg font-light">
                 Desde lanchas de performance até megaiates transoceânicos, nossa plataforma se adapta a cada necessidade.
               </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                { title: 'Sport & Day Cruisers', range: 'Até 45 pés', desc: 'Agilidade e luxo para navegação costeira e lazer rápido.' },
                { title: 'Executive Yachts', range: '46 a 79 pés', desc: 'O equilíbrio perfeito entre conforto transoceânico e sofisticação.' },
                { title: 'Superyachts', range: '80 pés+', desc: 'O ápice da engenharia naval com gestão total de compliance.' }
              ].map((cat, i) => (
                <div key={i} className="bg-white/[0.02] border border-white/5 p-12 rounded-sm hover:bg-white/[0.04] hover:border-[#c5a059]/30 transition-all group">
                   <Star size={24} className="text-[#c5a059]/20 mb-8 group-hover:text-[#c5a059] transition-all" />
                   <h3 className="text-xl font-serif font-bold text-white mb-2 tracking-tight uppercase tracking-widest">{cat.title}</h3>
                   <p className="text-[#c5a059] text-[10px] font-black tracking-[0.3em] uppercase mb-6">{cat.range}</p>
                   <p className="text-white/30 text-sm leading-relaxed">{cat.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 bg-gradient-to-b from-[#010c20] to-[#021431]">
           <div className="max-w-4xl mx-auto px-6 text-center border border-[#c5a059]/20 p-20 rounded-sm bg-[#c5a059]/5 backdrop-blur-xl relative overflow-hidden">
              <div className="absolute -top-20 -right-20 w-64 h-64 bg-[#c5a059]/10 blur-[80px] rounded-full"></div>
              <h2 className="text-4xl font-serif font-bold text-white mb-8 tracking-tight">Pronto para elevar o status da sua frota?</h2>
              <p className="text-white/50 mb-12 text-lg font-light">
                Junte-se às marinas e proprietários que já utilizam o padrão mundial de custódia digital.
              </p>
              <Link to="/login" className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-12 py-5 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all inline-flex items-center gap-4 shadow-2xl">
                 Registrar meu Ativo
                 <ArrowRight size={18} />
              </Link>
           </div>
        </section>
      </main>

      <footer className="py-20 border-t border-white/5 text-center">
         <p className="text-[10px] text-white/20 uppercase tracking-[0.5em]">Yachts Atlas • Excellence in Motion</p>
      </footer>
    </div>
  )
}
