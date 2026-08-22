import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import styles from './MarinaParceira.module.css';
import Header from '../components/Header';
import { api } from '../services/api';

export default function MarinaParceira() {
  const [form, setForm] = useState({
    marina: '',
    name: '',
    email: '',
    whatsapp: '',
    fleet: '',
    source: '',
  });
  const [errors, setErrors] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: false }));
  };

  const handleSubmit = async () => {
    // WhatsApp entra como obrigatorio: e por ele que a indicada e abordada.
    // Indicacao sem WhatsApp chega no painel e morre lá — vira lead que
    // ninguem consegue contatar.
    const required = ['marina', 'name', 'email', 'whatsapp', 'fleet', 'source'];
    const newErrors: Record<string, boolean> = {};
    required.forEach((key) => {
      if (!form[key as keyof typeof form].trim()) newErrors[key] = true;
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSubmitting(true);
    setSubmitError('');
    try {
      // 'oficial' fixo: esta pagina so existe no yachtsatlas.online. O mesmo
      // formulario roda na pagina de Lancamento, e sem isto as duas indicacoes
      // chegam identicas no banco — nao da para saber quem indicou de onde.
      await api.leads.marina({ ...form, origem: 'oficial' });
      setSubmitted(true);
    } catch {
      setSubmitError('Erro ao enviar. Tente novamente ou entre em contato por e-mail.');
    } finally {
      setSubmitting(false);
    }
  };

  // Tempo que a confirmação fica na tela, calibrado no uso real: 3s sumia
  // antes de terminar de ler, 7s deixava a página parada esperando à toa.
  const SEGUNDOS_DA_CONFIRMACAO = 4;

  // A confirmação aparece e o formulário volta limpo sozinho.
  // Sem isto a marina ficava presa na tela de sucesso, e indicar uma segunda
  // exigia recarregar a página — o programa vive de indicação, dificultar a
  // próxima trabalha contra o próprio produto.
  useEffect(() => {
    if (!submitted) return;
    const t = setTimeout(() => {
      setForm({ marina: '', name: '', email: '', whatsapp: '', fleet: '', source: '' });
      setErrors({});
      setSubmitError('');
      setSubmitted(false);
    }, SEGUNDOS_DA_CONFIRMACAO * 1000);
    // Se a marina sair da página antes do prazo, o timer morre junto: escrever
    // estado em componente desmontado é vazamento e vira aviso no console.
    return () => clearTimeout(t);
  }, [submitted]);

  // Contador real das 20 vagas fundadoras. Era `TAKEN_SPOTS = 12` chumbado no
  // código, contra um total de 120 — número inventado, e ainda por cima
  // contradizendo o próprio título da página. Se a leitura falhar, o bloco
  // some: melhor não mostrar contador nenhum do que mostrar um número errado
  // sobre escassez.
  const [vagas, setVagas] = useState<{ total: number; ocupadas: number } | null>(null);

  useEffect(() => {
    let ativo = true;
    api.leads.vagasFundadoras()
      .then((d) => { if (ativo) setVagas({ total: d.total, ocupadas: d.ocupadas }); })
      .catch(() => { if (ativo) setVagas(null); });
    return () => { ativo = false; };
  }, []);

  const fillPercent = vagas && vagas.total
    ? Math.round((vagas.ocupadas / vagas.total) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-[#010c20]">
      <Header />
      <div className="pt-[var(--header-h)]">
        <section className={styles.section}>
          <div className={styles.bgGlow} aria-hidden="true" />

          {/* Volta para a home: esta página é aberta a partir da dobra do
              Protocolo Genesis, então o visitante precisa de um caminho de
              retorno explícito — sem isso o único jeito é o botão do navegador. */}
          <Link to="/" className={styles.backLink}>
            <ArrowLeft size={14} />
            Voltar
          </Link>

          <span className={styles.eyebrow}>Programa de Indicação</span>

          <h2 className={styles.headline}>
            Sua indicação.<br />
            <em>Sua receita.</em>
          </h2>

          <p className={styles.subtext}>
            Indique uma marina para o Programa Atlas. Quando ela entrar na rede, 100% da receita dos
            dossiês que ela gerar é sua durante 12 meses — uma nova fonte de receita para a sua empresa.
          </p>

          {/* Alinhados à esquerda como o resto da coluna. Estavam centralizados
              no meio de uma seção sem largura máxima, e por isso flutuavam
              soltos, descolados do título e do texto. */}
          <p className="mt-2 text-[11px] font-black uppercase tracking-[0.22em] text-[#C9A84C]/80">
            Oferta oficial: USD 250/mês • Meta pública: 120 vagas
          </p>

          <div className="mt-8 p-5 border border-[#c5a059]/30 bg-[#c5a059]/5 rounded-sm max-w-3xl">
            <p className="text-[#E5D5B7] text-[10px] font-black uppercase tracking-[0.25em] mb-2">
              Cláusula Comercial de Indicação
            </p>
            <p className="text-white/70 text-sm leading-relaxed">
              Para marinas parceiras aprovadas: 100% da receita dos dossiês gerados pela marina indicada
              por 12 meses, contados da ativação da conta da indicada, conforme instrumento contratual.
            </p>
          </div>

          {vagas && (
            <div className={styles.spotsRow}>
              <div className={styles.spotsBar}>
                <div className={styles.spotsFill} style={{ width: `${fillPercent}%` }} />
              </div>
              <span className={styles.spotsText}>
                <strong>{vagas.ocupadas}</strong> de {vagas.total} vagas ocupadas
              </span>
            </div>
          )}

          <div className={styles.pillars}>
            {[
              {
                num: '01',
                title: 'Receita Imediata',
                text: (
                  <>
                    Cada dossiê gerado na sua marina representa{' '}
                    <strong>receita direta para o seu negócio</strong> — sem intermediários, sem burocracia.
                  </>
                ),
              },
              {
                num: '02',
                title: 'Indicação Rentável',
                text: (
                  <>
                    Marinas parceiras que indicam novos membros para a rede{' '}
                    <strong>participam dos dossiês gerados</strong> pela indicada durante o período fundador.
                  </>
                ),
              },
              {
                num: '03',
                title: 'Posição Oficial',
                text: (
                  <>
                    A página oficial trabalha a escala da rede com{' '}
                    <strong>120 vagas e mensalidade de USD 250</strong> para marinas em operação.
                  </>
                ),
              },
            ].map((p) => (
              <div key={p.num} className={styles.pillar}>
                <span className={styles.pillarNum}>{p.num}</span>
                <span className={styles.pillarTitle}>{p.title}</span>
                <p className={styles.pillarText}>{p.text}</p>
              </div>
            ))}
          </div>

          <div className={styles.formWrapper}>
            {!submitted ? (
              <>
                <div className={styles.formGrid}>
                  <div className={styles.field}>
                    <label className={styles.label}>Nome da Marina Indicada</label>
                    <input
                      className={`${styles.input} ${errors.marina ? styles.inputError : ''}`}
                      type="text"
                      name="marina"
                      placeholder="Marina do Porto"
                      value={form.marina}
                      onChange={handleChange}
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label}>Responsável</label>
                    <input
                      className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
                      type="text"
                      name="name"
                      placeholder="Nome completo"
                      value={form.name}
                      onChange={handleChange}
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label}>E-mail Corporativo</label>
                    <input
                      className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
                      type="email"
                      name="email"
                      placeholder="contato@marina.com.br"
                      value={form.email}
                      onChange={handleChange}
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label}>WhatsApp da Marina Indicada</label>
                    <input
                      className={`${styles.input} ${errors.whatsapp ? styles.inputError : ''}`}
                      type="tel"
                      name="whatsapp"
                      inputMode="tel"
                      placeholder="55 48 99999-1234"
                      value={form.whatsapp}
                      onChange={handleChange}
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label}>Porte da Frota</label>
                    <select
                      className={`${styles.select} ${errors.fleet ? styles.inputError : ''}`}
                      name="fleet"
                      value={form.fleet}
                      onChange={handleChange}
                    >
                      <option value="" disabled>Selecione</option>
                      <option value="1-20">1 – 20 embarcações</option>
                      <option value="21-50">21 – 50 embarcações</option>
                      <option value="51-100">51 – 100 embarcações</option>
                      <option value="100+">Acima de 100</option>
                    </select>
                  </div>

                  <div className={`${styles.field} ${styles.fieldFull}`}>
                    <label className={styles.label}>Sua Marina (quem está indicando)</label>
                    <input
                      className={`${styles.input} ${errors.source ? styles.inputError : ''}`}
                      type="text"
                      name="source"
                      placeholder="Nome da sua marina"
                      value={form.source}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className={styles.ctaRow}>
                  <p className={styles.disclaimer}>
                    A marina indicada será contatada pelo Atlas em até 48h, com a sua indicação
                    identificada. Aprovada a entrada dela na rede, os dossiês que ela gerar passam
                    a ser receita sua por 12 meses, conforme os termos comerciais aplicáveis.
                  </p>
                  {submitError && (
                    <p className="text-red-400 text-xs mb-4">{submitError}</p>
                  )}
                  <button className={styles.btn} onClick={handleSubmit} disabled={submitting}>
                    {submitting ? 'Enviando...' : 'Enviar Indicação →'}
                  </button>
                </div>
              </>
            ) : (
              <div className={styles.success}>
                <span className={styles.successIcon}>✦</span>
                <h3 className={styles.successTitle}>Indicação Recebida</h3>
                <p className={styles.successText}>
                  Vamos contatar a marina indicada em até 48 horas.<br />
                  Você é avisado assim que ela entrar na rede.
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
