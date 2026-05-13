import Header from '../components/Header'

export default function TermosFundadores() {
  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter']">
      <Header />
      <main className="pt-[166px] pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-serif font-bold mb-6">Termos do Programa Fundador</h1>
          <p className="text-white/60 mb-10">
            Condicoes comerciais referenciais para parceiros aprovados no ciclo fundador.
          </p>

          <div className="space-y-6 bg-white/[0.02] border border-white/10 p-8 rounded-sm">
            <section>
              <h2 className="text-[#c5a059] text-sm font-black uppercase tracking-[0.2em] mb-2">Receita de Dossies</h2>
              <p className="text-white/75 leading-relaxed">
                Parceiros fundadores aprovados operam com retencao integral da receita de dossies por 18 meses,
                contados da data de ativacao da conta, conforme contrato assinado entre as partes.
              </p>
            </section>

            <section>
              <h2 className="text-[#c5a059] text-sm font-black uppercase tracking-[0.2em] mb-2">Marco Inicial</h2>
              <p className="text-white/75 leading-relaxed">
                O periodo comercial inicia na ativacao operacional da conta parceira em ambiente de producao.
              </p>
            </section>

            <section>
              <h2 className="text-[#c5a059] text-sm font-black uppercase tracking-[0.2em] mb-2">Observacao</h2>
              <p className="text-white/75 leading-relaxed">
                Este texto possui carater informativo e deve refletir as condicoes finais descritas no instrumento contratual.
              </p>
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}
