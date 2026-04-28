import { Shield, CheckCircle, ArrowRight, History, Eye, ShieldCheck, Database, Lock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Header from '../components/Header'

export default function LandingPage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      <Header />

      {/* Hero Section */}
      <section className="relative h-[calc(100vh-180px)] mt-[180px] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0">
          <img 
            src="/hero-yacht.jpg" 
            alt="Luxury Yacht" 
            className="w-full h-full object-cover animate-slow-zoom brightness-[0.4]"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#010c20]/90 via-transparent to-[#010c20]"></div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#c5a059]/30 bg-[#c5a059]/5 backdrop-blur-sm mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
             <span className="w-1.5 h-1.5 rounded-full bg-[#c5a059] animate-pulse"></span>
             <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">{t('lp.hero_badge')}</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-serif font-bold text-white mb-8 tracking-tight leading-[0.95]">
            {t('lp.hero_title')} <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">
              {t('lp.hero_title_highlight')}
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-white/60 mb-12 max-w-2xl mx-auto leading-relaxed font-light">
            {t('lp.hero_subtitle')}
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Link 
              to="/login" 
              className="group bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-12 py-5 rounded-sm text-xs font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3 shadow-2xl shadow-[#c5a059]/10"
            >
              {t('lp.cta_start')}
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 opacity-30">
           <div className="w-px h-12 bg-gradient-to-b from-transparent to-white"></div>
           <span className="text-[8px] font-black tracking-[0.4em] uppercase">{t('common.scroll')}</span>
        </div>
      </section>

      {/* Dossier Levels Section */}
      <section className="py-32 relative bg-[#010c20]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-5xl font-serif font-bold text-white mb-6 tracking-tight">
              {t('lp.dossier_title')}
            </h2>
            <div className="w-24 h-1 bg-[#c5a059] mx-auto mb-8"></div>
            <p className="text-white/50 text-lg uppercase tracking-[0.2em] font-medium max-w-xl mx-auto">
              {t('lp.dossier_subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { level: 1, title: t('lp.level_1_title'), desc: t('lp.level_1_desc'), icon: Eye, tier: t('common.bronze') },
              { level: 2, title: t('lp.level_2_title'), desc: t('lp.level_2_desc'), icon: History, tier: t('common.silver') },
              { level: 3, title: t('lp.level_3_title'), desc: t('lp.level_3_desc'), icon: Shield, tier: t('common.gold') }
            ].map((item) => (
              <div 
                key={item.level}
                className="group relative bg-[#021431] border border-white/5 p-10 rounded-sm hover:bg-white/[0.05] hover:border-[#c5a059]/30 transition-all duration-500"
              >
                <div className="mb-8 flex items-center justify-between">
                   <div className="w-14 h-14 bg-[#c5a059]/10 rounded-full flex items-center justify-center text-[#c5a059]">
                     <item.icon size={24} />
                   </div>
                   <span className="text-[10px] font-black tracking-[0.3em] text-white/20 uppercase">{item.tier}</span>
                </div>
                <h3 className="text-2xl font-serif font-bold text-white mb-4 tracking-tight group-hover:text-[#c5a059] transition-colors">
                  {item.title}
                </h3>
                <p className="text-white/40 leading-relaxed text-sm">
                  {item.desc}
                </p>
                <div className="mt-8 pt-8 border-t border-white/5 flex items-center justify-between">
                   <div className="flex gap-1">
                      {[1, 2, 3].map(i => (
                        <div key={i} className={`w-6 h-0.5 rounded-full ${i <= item.level ? 'bg-[#c5a059]' : 'bg-white/5'}`}></div>
                      ))}
                   </div>
                   <button className="text-[10px] font-black tracking-[0.2em] text-[#c5a059] uppercase">
                     {t('common.explore')}
                   </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AUTHORITY SECTION */}
      <section className="py-40 bg-[#010c20] relative overflow-hidden border-y border-white/5">
        <div className="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
           <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#c5a059]/10 blur-[150px] rounded-full -translate-x-1/2 -translate-y-1/2"></div>
           <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-[#c5a059]/10 blur-[150px] rounded-full translate-x-1/2 translate-y-1/2"></div>
        </div>

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid lg:grid-cols-12 gap-16 items-center">
            <div className="lg:col-span-6 relative">
               <div className="relative rounded-sm overflow-hidden shadow-2xl group">
                 <img 
                   src="/interior-yacht.png" 
                   alt="Luxury Interior" 
                   className="w-full h-[600px] object-cover transition-transform duration-1000 group-hover:scale-105"
                 />
                 <div className="absolute bottom-8 left-8 right-8 bg-[#021431]/95 backdrop-blur-xl border border-[#c5a059]/30 p-8 rounded-sm shadow-2xl">
                    <div className="flex items-center gap-6 mb-6">
                       <img src="/logo-transparent.png" alt="Atlas Logo" className="w-16 h-auto" />
                       <div className="h-10 w-px bg-white/10"></div>
                       <div>
                         <p className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">{t('lp.trust_badge')}</p>
                         <p className="text-[8px] text-white/40 uppercase tracking-widest mt-1">{t('lp.trust_sub')}</p>
                       </div>
                    </div>
                    <p className="text-sm text-white/70 italic leading-relaxed font-serif">
                      "{t('lp.trust_quote')}"
                    </p>
                 </div>
               </div>
            </div>

            <div className="lg:col-span-6">
              <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8">
                 <ShieldCheck size={14} className="text-[#c5a059]" />
                 <span className="text-[10px] font-bold text-white uppercase tracking-widest">Universal Authority Protocol</span>
              </div>
              
              <h2 className="text-5xl md:text-6xl font-serif font-bold text-white mb-8 tracking-tight leading-tight">
                {t('lp.pricing_title')}
              </h2>
              
              <p className="text-white/50 text-lg mb-12 leading-relaxed font-light max-w-xl">
                {t('lp.pricing_subtitle')}
              </p>
              
              <div className="grid gap-6">
                {[
                  { title: t('lp.tech_1_title'), desc: t('lp.tech_1_desc'), icon: Database },
                  { title: t('lp.tech_2_title'), desc: t('lp.tech_2_desc'), icon: Lock },
                  { title: t('lp.tech_3_title'), desc: t('lp.tech_3_desc'), icon: ShieldCheck }
                ].map((feature, idx) => (
                  <div key={idx} className="flex gap-6 group p-6 rounded-sm hover:bg-white/[0.03] border border-transparent hover:border-white/10 transition-all">
                    <div className="flex-shrink-0 w-14 h-14 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                       <feature.icon size={24} />
                    </div>
                    <div>
                      <h4 className="text-white font-bold tracking-widest text-xs uppercase mb-2 group-hover:text-[#c5a059] transition-all">
                        {feature.title}
                      </h4>
                      <p className="text-white/40 text-sm leading-relaxed">{feature.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-16">
                 <button className="bg-white/5 hover:bg-[#c5a059] hover:text-[#010c20] border border-white/10 text-white px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all">
                   {t('lp.explore_protocol')}
                 </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 border-t border-white/5 bg-[#010c20] relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[200px] bg-[#c5a059]/5 blur-[100px] rounded-full pointer-events-none"></div>
        <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
          <img 
            src="/logo-transparent.png" 
            alt="Yachts Atlas" 
            className="w-[180px] object-contain mx-auto mb-8 opacity-80 hover:opacity-100 transition-all duration-700" 
          />
          <p className="text-[10px] font-black tracking-[0.5em] text-white/20 uppercase mb-8">
            {t('lp.footer_tagline')}
          </p>
          <div className="flex justify-center gap-8 mb-12">
            <a href="#" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.terms')}</a>
            <a href="#" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.privacy')}</a>
            <a href="#" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.contact')}</a>
          </div>
          <p className="text-[8px] text-white/10 uppercase tracking-widest">
            © {new Date().getFullYear()} Yachts Atlas. {t('lp.footer_copy')}
          </p>
        </div>
      </footer>
    </div>
  )
}
