import Header from '../components/Header'

/**
 * Política de Privacidade (LGPD).
 *
 * Conteúdo aterrado nos fluxos REAIS do sistema:
 *  - Banco e arquivos: Supabase (região Brasil — São Paulo).
 *  - Pagamentos: Stripe.
 *  - Assistente Solara: OpenAI (recebe apenas a pergunta sobre normas; PII é
 *    removida antes do envio — não trafega dado pessoal do titular).
 *  - Rastreamento técnico (IP, dispositivo, navegador) via middleware de
 *    auditoria/segurança.
 *
 * Encarregado (DPO) e prazos de retenção DECIDIDOS em 13/09/2026 — estão aqui e
 * em `conformidade/01-registro-de-operacoes-de-tratamento.md`, que é a fonte.
 * Mudou um prazo? Muda nos dois, ou a política pública passa a contradizer o
 * registro que a autoridade lê.
 *
 * O canal `dpo@yachtsatlas.online` precisa existir no provedor de e-mail: canal
 * publicado que não recebe é pior que canal nenhum.
 */

const VIGENCIA = '26 de junho de 2026'

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-[#c5a059] text-sm font-black uppercase tracking-[0.2em] mb-3">{titulo}</h2>
      <div className="text-white/75 leading-relaxed space-y-3">{children}</div>
    </section>
  )
}

export default function Privacidade() {
  return (
    <div className="min-h-screen bg-[#010c20] text-white">
      <Header />
      <main className="pt-[var(--header-h)] pb-24 px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-serif font-bold mb-3">Política de Privacidade</h1>
          <p className="text-white/40 text-sm mb-10">
            Em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 — LGPD).
            {' '}Vigência: {VIGENCIA}.
          </p>

          <div className="space-y-10 bg-white/[0.02] border border-white/10 p-8 md:p-10 rounded-sm">

            <Secao titulo="1. Quem é o controlador dos seus dados">
              <p>
                O <strong>Yachts Atlas</strong> (operado por <strong>AXOSHUB</strong>) é a plataforma de
                custódia digital de ativos náuticos responsável pelo tratamento dos dados pessoais
                descritos nesta política, na condição de <em>controlador</em>.
              </p>
              <p>
                Dúvidas, solicitações ou exercício de direitos podem ser direcionados ao nosso
                Encarregado pelo Tratamento de Dados (DPO), <strong>Marcos</strong>, sócio-fundador
                da AXOS HUB, pelo e-mail{' '}
                <a href="mailto:dpo@yachtsatlas.online" className="text-[#c5a059] hover:underline">
                  dpo@yachtsatlas.online
                </a>{' '}
                — respondemos em até 15 dias corridos.
              </p>
            </Secao>

            <Secao titulo="2. Quais dados coletamos">
              <p>Coletamos apenas o necessário para prestar o serviço:</p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  <strong>Cadastro e contato:</strong> nome, e-mail, telefone/WhatsApp e, quando aplicável,
                  CPF ou CNPJ. Para Marinas e parceiros: razão social, dados da empresa e do responsável.
                </li>
                <li>
                  <strong>Dados do ativo náutico:</strong> tipo, marca, modelo, ano, dimensões,
                  classificação e documentos, imagens e laudos enviados por você ou pela Marina.
                </li>
                <li>
                  <strong>Dados de pagamento:</strong> processados diretamente pela Stripe. Não
                  armazenamos o número completo do seu cartão em nossos servidores.
                </li>
                <li>
                  <strong>Dados técnicos de acesso:</strong> endereço IP, tipo de dispositivo, navegador,
                  idioma, páginas acessadas e data/hora — coletados automaticamente para segurança,
                  auditoria e bom funcionamento da plataforma.
                </li>
              </ul>
            </Secao>

            <Secao titulo="3. Para que usamos e com qual base legal">
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="text-white/40 text-left uppercase tracking-wider text-[11px]">
                      <th className="py-2 pr-4 border-b border-white/10">Finalidade</th>
                      <th className="py-2 border-b border-white/10">Base legal (LGPD, art. 7º)</th>
                    </tr>
                  </thead>
                  <tbody className="text-white/75">
                    <tr><td className="py-2 pr-4 border-b border-white/5">Criar e manter sua conta e prestar o serviço de custódia e dossiê</td><td className="py-2 border-b border-white/5">Execução de contrato</td></tr>
                    <tr><td className="py-2 pr-4 border-b border-white/5">Emitir cobranças e cumprir obrigações fiscais/contábeis</td><td className="py-2 border-b border-white/5">Obrigação legal</td></tr>
                    <tr><td className="py-2 pr-4 border-b border-white/5">Segurança, prevenção a fraude, auditoria e registros de acesso</td><td className="py-2 border-b border-white/5">Legítimo interesse</td></tr>
                    <tr><td className="py-2 pr-4 border-b border-white/5">Responder solicitações enviadas por formulários (leads/parceria)</td><td className="py-2 border-b border-white/5">Diligências pré-contratuais</td></tr>
                    <tr><td className="py-2 pr-4">Comunicações de marketing (quando houver)</td><td className="py-2">Consentimento</td></tr>
                  </tbody>
                </table>
              </div>
            </Secao>

            <Secao titulo="4. Com quem compartilhamos">
              <p><strong>Não vendemos seus dados.</strong> Compartilhamos apenas com operadores essenciais à operação:</p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Supabase</strong> — banco de dados e armazenamento de arquivos (infraestrutura em região do Brasil — São Paulo).</li>
                <li><strong>Stripe</strong> — processamento de pagamentos.</li>
                <li>
                  <strong>OpenAI</strong> — apenas para a assistente de normas (Capitã Solara). Ela recebe
                  somente a sua pergunta sobre normas; dados pessoais identificados na mensagem são
                  removidos antes do envio e a assistente não acessa dados de Marinas, proprietários ou
                  embarcações específicas.
                </li>
                <li><strong>Autoridades públicas</strong> — quando exigido por lei ou ordem judicial.</li>
              </ul>
            </Secao>

            <Secao titulo="5. Transferência internacional de dados">
              <p>
                Alguns operadores (como Stripe e OpenAI) processam dados fora do Brasil. Nesses casos,
                a transferência ocorre com salvaguardas contratuais e técnicas adequadas, conforme a
                LGPD. Os dados do banco e os arquivos do seu dossiê ficam hospedados em infraestrutura
                localizada no Brasil.
              </p>
            </Secao>

            <Secao titulo="6. Por quanto tempo guardamos">
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Conta ativa:</strong> enquanto você utilizar o serviço.</li>
                <li><strong>Após o encerramento:</strong> o histórico custodiado permanece por <strong>5 anos</strong> e então é anonimizado — o registro do serviço continua existindo, os dados pessoais saem dele.</li>
                <li><strong>Contato comercial que não virou cliente:</strong> eliminado após <strong>12 meses</strong> sem qualquer interação.</li>
                <li><strong>Registros de acesso e segurança</strong> (IP, navegador): <strong>6 meses</strong>, na forma do art. 15 do Marco Civil da Internet.</li>
                <li><strong>Registros fiscais e financeiros:</strong> pelos prazos legais aplicáveis.</li>
              </ul>
            </Secao>

            <Secao titulo="7. Seus direitos como titular (LGPD, art. 18)">
              <p>Você pode, a qualquer momento, solicitar:</p>
              <ul className="list-disc pl-5 space-y-2">
                <li>Confirmação da existência de tratamento e acesso aos seus dados;</li>
                <li>Correção de dados incompletos, inexatos ou desatualizados;</li>
                <li>Anonimização, bloqueio ou eliminação de dados desnecessários ou tratados em desconformidade;</li>
                <li>Portabilidade dos dados;</li>
                <li>Informação sobre com quem compartilhamos seus dados;</li>
                <li>Revogação do consentimento, quando esta for a base legal.</li>
              </ul>
              <p>
                Para exercer seus direitos, escreva para{' '}
                <a href="mailto:dpo@yachtsatlas.online" className="text-[#c5a059] hover:underline">
                  dpo@yachtsatlas.online
                </a>. Você também pode apresentar reclamação à ANPD (Autoridade Nacional de Proteção de Dados).
              </p>
            </Secao>

            <Secao titulo="8. Como protegemos seus dados">
              <ul className="list-disc pl-5 space-y-2">
                <li>Criptografia em trânsito (TLS) e em repouso na infraestrutura de armazenamento;</li>
                <li>Verificação de integridade dos documentos por hash SHA-256;</li>
                <li>Controle de acesso por papéis e isolamento de dados por linha (RLS) no banco;</li>
                <li>Registros de auditoria e monitoramento de acessos não autorizados.</li>
              </ul>
            </Secao>

            <Secao titulo="9. Cookies e tecnologias de rastreamento">
              <p>
                Utilizamos cookies <strong>essenciais</strong> para manter sua sessão autenticada e o
                funcionamento da plataforma. Coletamos dados técnicos de acesso (IP, dispositivo) com
                base no legítimo interesse de segurança e auditoria. No momento, não utilizamos
                ferramentas de publicidade de terceiros; caso passemos a usar análise/medição não
                essencial, solicitaremos o seu consentimento.
              </p>
            </Secao>

            <Secao titulo="10. Menores de idade">
              <p>
                O serviço é destinado a maiores de 18 anos e não coletamos intencionalmente dados de
                menores. Se identificarmos esse tipo de dado, ele será eliminado.
              </p>
            </Secao>

            <Secao titulo="11. Alterações nesta política">
              <p>
                Podemos atualizar esta política para refletir mudanças no serviço ou na legislação.
                Mudanças relevantes serão comunicadas pelos nossos canais, e a data de vigência acima
                será atualizada.
              </p>
            </Secao>

            <Secao titulo="12. Contato">
              <p>
                Encarregado pelo Tratamento de Dados (DPO): Marcos, sócio-fundador da AXOS HUB —{' '}
                <a href="mailto:dpo@yachtsatlas.online" className="text-[#c5a059] hover:underline">
                  dpo@yachtsatlas.online
                </a>
                <br />
                Yachts Atlas — operado por AXOSHUB.
              </p>
            </Secao>

          </div>
        </div>
      </main>
    </div>
  )
}
