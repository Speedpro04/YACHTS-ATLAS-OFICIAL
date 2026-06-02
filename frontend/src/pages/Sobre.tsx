import { Link } from 'react-router-dom'
import { Gauge, Camera, FileText, ClipboardCheck, Lock, Anchor, ArrowRight } from 'lucide-react'
import Header from '../components/Header'

export default function Sobre() {
  const cobertura = [
    {
      icon: Camera,
      titulo: 'Registro Fotográfico',
      texto: 'Imagens de cada parte do ativo — datadas, geolocalizadas e seladas. O estado registrado naquele momento, para sempre.',
    },
    {
      icon: FileText,
      titulo: 'Documentação & Procedência',
      texto: 'Documentos legais, fiscais e histórico de propriedade organizados em cofre digital — cada arquivo vinculado, datado e à prova de adulteração.',
    },
    {
      icon: Gauge,
      titulo: 'Histórico Mecânico',
      texto: 'Manutenções, motorização e serviços registrados ao longo do tempo, formando a memória técnica completa do ativo.',
    },
    {
      icon: ClipboardCheck,
      titulo: 'Laudos de Terceiros',
      texto: 'Inspeções e laudos emitidos por profissionais e estaleiros são custodiados no dossiê — nós guardamos e certificamos, com fé na origem.',
    },
    {
      icon: Lock,
      titulo: 'Selo de Integridade SHA-256',
      texto: 'Cada registro recebe uma assinatura criptográfica. Se algo mudar, fica evidente. É a garantia de que o histórico não foi alterado.',
    },
    {
      icon: Anchor,
      titulo: 'Pronto para Seguradoras',
      texto: 'A história consolidada e verificável reduz a assimetria de risco — base sólida para precificação e renovação de apólice.',
    },
  ]

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      <Header />

      <main className="mt-[var(--header-h)]">
        {/* Hero */}
        <section className="relative py-32 md:py-40 overflow-hidden border-b border-white/5">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-[#c5a059]/5 blur-[140px] rounded-full pointer-events-none"></div>
          <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#c5a059]/30 bg-[#c5a059]/5 mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-[#c5a059]"></span>
              <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">A Casa Técnica da Náutica</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-serif font-bold text-white mb-8 tracking-tight leading-[1.05]">
              Não inspecionamos. <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">Custodiamos</span> a verdade do seu ativo.
            </h1>
            <p className="text-lg md:text-xl text-white/60 leading-relaxed font-light max-w-2xl mx-auto">
              Um ativo náutico vale o que sua história prova. O Yachts Atlas documenta, organiza e blinda essa história — cada documento, cada imagem, datado, geolocalizado e à prova de fraude.
            </p>
          </div>
        </section>

        {/* Posicionamento */}
        <section className="py-24 border-b border-white/5">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <p className="text-xl md:text-2xl text-white/70 font-light leading-relaxed font-serif italic">
              Somos o cartório digital do ativo náutico. Reunimos a documentação, as imagens
              e os laudos de cada embarcação e os tornamos permanentes, verificáveis e
              impossíveis de adulterar.
            </p>
          </div>
        </section>

        {/* O Coração Mecânico */}
        <section className="py-28 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-[#c5a059]/5 blur-[120px] rounded-full pointer-events-none"></div>
          <div className="max-w-5xl mx-auto px-6 relative z-10">
            <div className="flex flex-col md:flex-row items-start gap-12">
              <div className="flex-shrink-0">
                <div className="w-20 h-20 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059]">
                  <Gauge size={40} strokeWidth={1.5} />
                </div>
              </div>
              <div>
                <span className="block text-[10px] font-black tracking-[0.4em] text-[#c5a059] uppercase mb-4">O Coração Mecânico</span>
                <h2 className="text-3xl md:text-4xl font-serif font-bold text-white mb-6 tracking-tight leading-tight">
                  O motor é a alma de uma embarcação.
                </h2>
                <p className="text-white/50 text-lg font-light leading-relaxed mb-6">
                  É onde a engenharia se torna movimento, e onde nasce ou se perde a confiança de quem navega.
                  Por isso damos à motorização o registro que ela merece — cada manutenção, cada serviço,
                  cada hora de operação, documentado por quem entende a importância de cada detalhe.
                </p>
                <p className="text-white/50 text-lg font-light leading-relaxed">
                  Um motor bem documentado não é só um item do dossiê. É a prova de que aquele ativo foi
                  cuidado ao longo do tempo.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Cobertura Técnica */}
        <section className="py-28 bg-white/[0.01] border-y border-white/5">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-20">
              <h2 className="text-3xl md:text-4xl font-serif font-bold text-white mb-6 tracking-tight">
                Cobrimos o ativo de ponta a ponta.
              </h2>
              <div className="w-24 h-1 bg-[#c5a059] mx-auto mb-8"></div>
              <p className="text-white/50 max-w-2xl mx-auto font-light leading-relaxed">
                O dono e a marina reúnem o que têm; os laudos de terceiros entram no mesmo cofre.
                Tudo organizado, datado e selado — uma memória única e à prova de fraude do ativo.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {cobertura.map((item, i) => (
                <div key={i} className="group bg-[#021431] border border-white/5 p-8 rounded-sm hover:border-[#c5a059]/30 transition-all duration-500 shadow-xl">
                  <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] mb-6 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                    <item.icon size={22} strokeWidth={1.5} />
                  </div>
                  <h3 className="text-lg font-serif font-bold text-white mb-3 tracking-tight group-hover:text-[#c5a059] transition-colors">
                    {item.titulo}
                  </h3>
                  <p className="text-white/40 text-sm leading-relaxed font-light">
                    {item.texto}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Frase de Força */}
        <section className="py-32 relative overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-[#c5a059]/5 blur-[130px] rounded-full pointer-events-none"></div>
          <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
            <p className="text-4xl md:text-6xl font-serif font-bold text-white tracking-tight leading-tight">
              Documentado uma vez.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] italic">Verdadeiro para sempre.</span>
            </p>
          </div>
        </section>

        {/* A Origem */}
        <section className="py-28 bg-white/[0.01] border-y border-white/5">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <span className="block text-[10px] font-black tracking-[0.4em] text-[#c5a059] uppercase mb-8">A Origem</span>
            <p className="text-xl md:text-2xl text-white/70 font-light leading-relaxed font-serif">
              Há por trás do Atlas a trajetória de quem passou a vida medindo, inspecionando e construindo
              com as próprias mãos — do torno mecânico ao ultrassom, da prancheta técnica à marcenaria, e de
              uma paixão genuína por motores.
            </p>
            <p className="text-white/40 text-lg font-light leading-relaxed mt-8">
              É essa bagagem que define o nosso padrão de documentação — registrar a história de um
              ativo com o rigor de quem sabe, na prática, o que realmente importa.
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="py-28">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h2 className="text-3xl md:text-4xl font-serif font-bold text-white mb-6 tracking-tight">
              Conheça o padrão Atlas.
            </h2>
            <p className="text-white/50 font-light mb-12 max-w-xl mx-auto leading-relaxed">
              Um dossiê construído com rigor de engenharia, para proteger e valorizar o seu patrimônio náutico.
            </p>
            <Link
              to="/marina-parceira"
              className="inline-flex items-center gap-3 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-12 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all shadow-2xl shadow-[#c5a059]/10"
            >
              Seja uma Marina Parceira
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-16 border-t border-white/5 bg-[#010c20]">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <img src="/logo-transparent.png" alt="Yachts Atlas" className="w-[150px] object-contain mx-auto mb-6 opacity-70" />
          <p className="text-[9px] text-white/20 uppercase tracking-[0.4em]">
            Yachts Atlas — Custódia Digital de Ativos Náuticos
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
