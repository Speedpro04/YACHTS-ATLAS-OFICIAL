import { ArrowRight, Eye, ShieldCheck, Database, Lock, TrendingUp, Zap, Anchor, Camera, FileText, History, ChevronDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import Header from '../components/Header'
import { FAIXAS_DOSSIE, formatarPreco } from '../config/precosDossie'

const FAQS = [
  {
    q: 'Meu jet ski ou lancha pequena tem dossiê?',
    a: 'Sim. Todo ativo náutico até 26 pés — incluindo jet skis, motos aquáticas e embarcações de pequeno porte, motorizadas ou não — entra na faixa de entrada do Dossiê Yachts Atlas, a partir de US$ 100.',
  },
  {
    q: 'Quanto custa o dossiê?',
    a: 'O preço acompanha o porte do ativo, de US$ 100 (até 26 pés) a US$ 1.500 (acima de 150 pés). É um dossiê único e completo — o valor varia apenas pela complexidade do ativo, nunca pela qualidade do documento.',
  },
  {
    q: 'O Yachts Atlas inspeciona a embarcação?',
    a: 'Não. Somos a custódia digital do ativo: reunimos, organizamos e blindamos documentos, imagens e laudos. Inspeções, quando existem, são feitas por profissionais e estaleiros — nós guardamos e certificamos a integridade desses registros.',
  },
  {
    q: 'O que entra no dossiê?',
    a: 'Identificação e procedência, histórico de propriedade, documentação legal, histórico de manutenção e motorização, registro fotográfico datado e geolocalizado, e os laudos de terceiros — tudo selado e organizado em um único cofre digital.',
  },
  {
    q: 'Por quanto tempo o dossiê fica disponível?',
    a: 'O dossiê é permanente. Cada registro é preservado de forma imutável, formando a memória definitiva do ativo ao longo de toda a sua vida.',
  },
  {
    q: 'Como sei que o dossiê não foi adulterado?',
    a: 'Cada registro recebe uma assinatura criptográfica SHA-256 no momento em que entra no cofre. Qualquer alteração posterior fica evidente — é a sua garantia de autenticidade.',
  },
  {
    q: 'Sou uma marina. Como funciona a parceria?',
    a: 'A marina integra-se à rede Atlas e passa a oferecer dossiês à sua frota, com condições fundadoras exclusivas. Solicite o credenciamento pelo programa de Marina Parceira.',
  },
]

export default function LandingPage() {
  const { t } = useTranslation()
  const [openFaq, setOpenFaq] = useState<number | null>(0)

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      <Header />

      {/* Hero Section */}
      <section className="relative min-h-[calc(100vh-var(--header-h))] mt-[var(--header-h)] flex items-center justify-center overflow-hidden py-[50px]">
        <div className="absolute inset-0">
          <img
            src="/hero-yacht-v2-light.jpg"
            alt="Iate de luxo ancorado — custódia digital de ativos náuticos Yachts Atlas"
            className="w-full h-full object-cover animate-slow-zoom"
            loading="eager"
            fetchPriority="high"
          />
          <div className="absolute inset-0 bg-[#010c20]/[0.9]"></div>
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

          {/* Um único dossiê — sem classes */}
          <div className="max-w-3xl mx-auto text-center mb-20">
            <p className="text-white/60 text-lg font-light leading-relaxed">
              Não existem versões "básica" ou "premium". Existe{' '}
              <span className="text-[#c5a059] font-medium">um único Dossiê Yachts Atlas</span> —
              a custódia digital que reúne, organiza e blinda toda a história do seu ativo.
              Cada documento, cada imagem, cada registro: datado, geolocalizado e à prova de fraude.
            </p>
          </div>

          {/* Pilares — o que todo dossiê sempre reúne */}
          <div className="text-center mb-12">
            <span className="text-[10px] font-black tracking-[0.4em] text-[#c5a059] uppercase">O que todo dossiê reúne</span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-24">
            {[
              { icon: Camera, label: 'Registro Fotográfico', sub: 'Datado e geolocalizado' },
              { icon: FileText, label: 'Documentação & Procedência', sub: 'Cofre digital' },
              { icon: History, label: 'Histórico Completo', sub: 'Manutenção e motorização' },
              { icon: Lock, label: 'Selo de Integridade', sub: 'SHA-256 imutável' },
            ].map((f, i) => (
              <div key={i} className="bg-[#021431] border border-white/5 p-6 rounded-sm text-center group hover:border-[#c5a059]/30 transition-all duration-500">
                <div className="w-12 h-12 mx-auto bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] mb-4 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                  <f.icon size={20} />
                </div>
                <p className="text-white text-sm font-bold tracking-wide">{f.label}</p>
                <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] font-black mt-1">{f.sub}</p>
              </div>
            ))}
          </div>

          {/* Escada de preços — 8 faixas por porte */}
          <div className="text-center mb-12">
            <h3 className="text-2xl md:text-3xl font-serif font-bold text-white mb-3 tracking-tight">
              O preço acompanha o porte do ativo
            </h3>
            <p className="text-white/40 text-[11px] uppercase tracking-[0.3em] font-black">
              Da lancha ao megayacht — sempre a mesma excelência
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto">
            {FAIXAS_DOSSIE.map((faixa) => (
              <div key={faixa.id} className="bg-white/[0.02] border border-white/5 p-6 rounded-sm text-center hover:border-[#c5a059]/40 hover:bg-white/[0.04] transition-all duration-500">
                <p className="text-[10px] text-white/40 uppercase tracking-[0.2em] font-black mb-3">{faixa.label}</p>
                <p className="text-2xl font-serif font-bold text-[#c5a059]">{formatarPreco(faixa.precoUSD)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY CHOOSE US SECTION */}
      <section className="py-32 bg-white/[0.01] border-y border-white/5 relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-64 h-64 bg-[#c5a059]/5 blur-[100px] rounded-full -translate-x-1/2 -translate-y-1/2"></div>
        
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-end justify-between mb-20 gap-8">
            <div className="max-w-2xl">
               <h2 className="text-4xl md:text-5xl font-serif font-bold text-white mb-6 tracking-tight leading-tight">
                 {t('lp.why_atlas_title')}
               </h2>
               <p className="text-white/40 text-lg font-light uppercase tracking-widest">
                 {t('lp.why_atlas_subtitle')}
               </p>
            </div>
            <div className="h-px flex-1 bg-white/5 mx-12 hidden md:block"></div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { id: 1, title: t('lp.benefit_1_title'), desc: t('lp.benefit_1_desc'), icon: TrendingUp },
              { id: 2, title: t('lp.benefit_2_title'), desc: t('lp.benefit_2_desc'), icon: Zap },
              { id: 3, title: t('lp.benefit_3_title'), desc: t('lp.benefit_3_desc'), icon: ShieldCheck },
              { id: 4, title: t('lp.benefit_4_title'), desc: t('lp.benefit_4_desc'), icon: Anchor }
            ].map((benefit) => (
              <div key={benefit.id} className="group p-8 bg-[#021431] border border-white/5 rounded-sm hover:border-[#c5a059]/30 transition-all duration-700 shadow-2xl">
                 <div className="w-12 h-12 bg-[#c5a059]/5 border border-[#c5a059]/10 flex items-center justify-center text-[#c5a059] mb-8 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                    <benefit.icon size={20} />
                 </div>
                 <h4 className="text-white font-bold uppercase tracking-[0.2em] text-[10px] mb-4 group-hover:text-[#c5a059] transition-all">
                    {benefit.title}
                 </h4>
                 <p className="text-white/30 text-sm leading-relaxed font-light">
                    {benefit.desc}
                 </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PARTNERS SECTION */}
      <section className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-serif font-bold text-white mb-4 tracking-tight">{t('lp.partners_title')}</h2>
            <p className="text-white/40 uppercase tracking-[0.3em] text-[10px] font-black">{t('lp.partners_subtitle')}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-12">
            <div className="group bg-gradient-to-br from-[#021431] to-[#010c20] border border-white/5 p-12 rounded-sm hover:border-[#c5a059]/40 transition-all duration-700 relative overflow-hidden">
               <div className="absolute top-0 right-0 w-32 h-32 bg-[#c5a059]/5 blur-[60px] rounded-full translate-x-1/2 -translate-y-1/2"></div>
               <div className="relative z-10">
                  <div className="w-16 h-16 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] mb-8 group-hover:scale-110 transition-transform">
                     <Zap size={28} />
                  </div>
                  <h3 className="text-2xl font-serif font-bold text-white mb-6 tracking-tight">{t('lp.partners_broker_title')}</h3>
                  <p className="text-white/40 leading-relaxed mb-8 font-light">
                    {t('lp.partners_broker_desc')}
                  </p>
                  <button className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase flex items-center gap-2 group/btn">
                    {t('common.broker_network')} <ArrowRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
                  </button>
               </div>
            </div>

            <div className="group bg-gradient-to-br from-[#021431] to-[#010c20] border border-white/5 p-12 rounded-sm hover:border-[#c5a059]/40 transition-all duration-700 relative overflow-hidden">
               <div className="absolute top-0 right-0 w-32 h-32 bg-[#c5a059]/5 blur-[60px] rounded-full translate-x-1/2 -translate-y-1/2"></div>
               <div className="relative z-10">
                  <div className="w-16 h-16 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] mb-8 group-hover:scale-110 transition-transform">
                     <ShieldCheck size={28} />
                  </div>
                  <h3 className="text-2xl font-serif font-bold text-white mb-6 tracking-tight">{t('lp.partners_insurance_title')}</h3>
                  <p className="text-white/40 leading-relaxed mb-8 font-light">
                    {t('lp.partners_insurance_desc')}
                  </p>
                  <button className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase flex items-center gap-2 group/btn">
                    {t('common.insurance_network')} <ArrowRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
                  </button>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* CURIOSITY TEASER SECTION - THE GENESIS PROTOCOL */}
      <section className="py-40 bg-[#010c20] relative overflow-hidden border-t border-white/5 flex items-center justify-center">
         <div className="absolute inset-0 bg-[url('/fleet-hero-light.jpg')] bg-cover bg-center opacity-5 mix-blend-luminosity"></div>
         <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-[#010c20]/80 to-[#010c20]"></div>
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c5a059]/5 blur-[150px] rounded-full pointer-events-none"></div>
         
         <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
            <div className="w-16 h-16 mx-auto bg-[#c5a059]/5 border border-[#c5a059]/20 flex items-center justify-center mb-10 relative group cursor-pointer hover:border-[#c5a059]/50 transition-all duration-700">
               <div className="absolute inset-0 bg-[#c5a059] opacity-0 group-hover:opacity-10 transition-opacity duration-700"></div>
               <Lock size={20} className="text-[#c5a059] group-hover:scale-110 transition-transform duration-700" />
            </div>
            
            <h2 className="text-5xl md:text-7xl font-serif font-bold text-white mb-8 tracking-tight leading-tight">
               O Protocolo <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">Genesis.</span>
            </h2>
            
            <p className="text-white/40 text-lg md:text-xl mb-16 font-light leading-relaxed max-w-2xl mx-auto">
               Não aceitamos qualquer marina. Estamos selecionando rigorosamente 40 parceiros fundadores para operar com um modelo de negócio que nunca mais será repetido.
            </p>
            
            <div className="inline-block p-[1px] bg-gradient-to-b from-white/10 via-[#c5a059]/30 to-transparent rounded-sm relative group">
               <div className="absolute -inset-2 bg-gradient-to-r from-[#c5a059]/0 via-[#c5a059]/10 to-[#c5a059]/0 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
               <div className="bg-[#021431]/90 px-12 py-10 rounded-sm backdrop-blur-xl relative z-10 border border-[#010c20]">
                  <div className="flex items-center justify-center gap-3 mb-6">
                     <span className="w-1.5 h-1.5 rounded-full bg-[#c5a059] animate-pulse"></span>
                     <p className="text-[10px] text-[#c5a059] font-black uppercase tracking-[0.4em]">Confidencial</p>
                  </div>
                  
                  <p className="text-white/80 text-sm mb-10 font-light max-w-sm mx-auto">
                     O que acontece quando você se torna um parceiro fundador do Yachts Atlas?
                  </p>
                  
                  <Link 
                    to="/marina-parceira" 
                    className="inline-flex items-center gap-4 bg-transparent border border-[#c5a059]/50 hover:bg-[#c5a059] hover:border-[#c5a059] hover:text-[#010c20] text-[#c5a059] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all duration-500 overflow-hidden relative"
                  >
                     <span className="relative z-10 flex items-center gap-3">
                       Desbloquear Arquivo
                       <Eye size={14} />
                     </span>
                  </Link>
               </div>
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
               <div className="relative rounded-sm group">
                 <img
                   src="/turquoise-yacht-light.jpg"
                   alt="Superiate em águas turquesa — autoridade e padrão Yachts Atlas"
                   className="w-full h-[600px] object-cover transition-transform duration-1000 group-hover:scale-105"
                   loading="lazy"
                   width={800}
                   height={600}
                 />
                 <div className="absolute bottom-[-118px] left-8 right-8 z-20 bg-[#021431]/95 backdrop-blur-xl border border-[#c5a059]/30 p-8 rounded-sm shadow-2xl">
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

              <div className="mt-10 p-6 border border-[#c5a059]/30 bg-[#c5a059]/5 rounded-sm">
                <p className="text-[#E5D5B7] text-[10px] font-black uppercase tracking-[0.25em] mb-2">
                  Founder Contract Benefit
                </p>
                <p className="text-white/70 text-sm leading-relaxed">
                  Parceiros fundadores aprovados recebem condicao comercial dedicada:
                  receita de dossies em modelo de retencao integral por 18 meses, conforme contrato.
                </p>
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

      {/* FAQ */}
      <section className="py-32 bg-[#010c20] border-t border-white/5 relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-64 h-64 bg-[#c5a059]/5 blur-[120px] rounded-full -translate-y-1/2 pointer-events-none"></div>
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <div className="text-center mb-16">
            <span className="block text-[10px] font-black tracking-[0.4em] text-[#c5a059] uppercase mb-6">Perguntas Frequentes</span>
            <h2 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight">
              Do jet ski ao megayacht.
            </h2>
          </div>

          <div className="space-y-4">
            {FAQS.map((faq, i) => {
              const isOpen = openFaq === i
              return (
                <div key={i} className="bg-[#021431] border border-white/5 rounded-sm overflow-hidden transition-all duration-500 hover:border-[#c5a059]/20">
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className="w-full flex items-center justify-between gap-6 px-8 py-6 text-left group"
                    aria-expanded={isOpen}
                  >
                    <span className={`text-base md:text-lg font-serif font-bold tracking-tight transition-colors ${isOpen ? 'text-[#c5a059]' : 'text-white group-hover:text-[#c5a059]'}`}>
                      {faq.q}
                    </span>
                    <ChevronDown
                      size={20}
                      className={`flex-shrink-0 text-[#c5a059] transition-transform duration-500 ${isOpen ? 'rotate-180' : ''}`}
                    />
                  </button>
                  <div className={`px-8 transition-all duration-500 ${isOpen ? 'max-h-96 pb-7 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
                    <p className="text-white/50 text-sm md:text-[15px] leading-relaxed font-light">
                      {faq.a}
                    </p>
                  </div>
                </div>
              )
            })}
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
            <Link to="/termos-fundadores" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.terms')}</Link>
            <a href="#" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.privacy')}</a>
            <a href="#" className="text-[10px] font-bold text-white/30 hover:text-[#c5a059] uppercase tracking-widest transition-all">{t('lp.contact')}</a>
          </div>
          <p className="text-[8px] text-white/10 uppercase tracking-widest">
            © {new Date().getFullYear()} Yachts Atlas. {t('lp.footer_copy')}
          </p>
          <p className="text-[8px] text-white/15 uppercase tracking-[0.3em] mt-4">
            Desenvolvido pela{' '}
            <a
              href="https://axoshub.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/30 hover:text-[#c5a059] font-bold transition-all"
            >
              AXOS HUB
            </a>{' '}
            — Arquitetura Digital
          </p>
        </div>
      </footer>
    </div>
  )
}
