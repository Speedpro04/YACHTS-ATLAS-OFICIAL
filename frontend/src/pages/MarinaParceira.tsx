import { useEffect, useState } from 'react';
import styles from './MarinaParceira.module.css';
import Header from '../components/Header';
import { api } from '../services/api';

export default function MarinaParceira() {
  const [form, setForm] = useState({
    marina: '',
    name: '',
    email: '',
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
    const required = ['marina', 'name', 'email', 'fleet'];
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
      await api.leads.marina(form);
      setSubmitted(true);
    } catch {
      setSubmitError('Erro ao enviar. Tente novamente ou entre em contato por e-mail.');
    } finally {
      setSubmitting(false);
    }
  };

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

          <span className={styles.eyebrow}>20 Vagas Fundadoras</span>

          <h2 className={styles.headline}>
            Sua marina.<br />
            <em>Sua receita.</em>
          </h2>

          <p className={styles.subtext}>
            As primeiras marinas a integrar a rede Atlas operam em condições fundadoras — benefícios
            exclusivos que não estarão disponíveis para novos parceiros após o encerramento desta fase.
          </p>

          {/* Alinhados à esquerda como o resto da coluna. Estavam centralizados
              no meio de uma seção sem largura máxima, e por isso flutuavam
              soltos, descolados do título e do texto. */}
          <p className="mt-2 text-[11px] font-black uppercase tracking-[0.22em] text-[#C9A84C]/80">
            Oferta oficial: USD 250/mês • Meta pública: 120 vagas
          </p>

          <div className="mt-8 p-5 border border-[#c5a059]/30 bg-[#c5a059]/5 rounded-sm max-w-3xl">
            <p className="text-[#E5D5B7] text-[10px] font-black uppercase tracking-[0.25em] mb-2">
              Clausula Comercial de Dossies
            </p>
            <p className="text-white/70 text-sm leading-relaxed">
              Para parceiros fundadores aprovados: receita de dossies com retencao integral por 18 meses,
              contados da ativacao da conta, conforme instrumento contratual.
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
                    <label className={styles.label}>Nome da Marina</label>
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
                    <label className={styles.label}>Como conheceu o Atlas Yachts?</label>
                    <input
                      className={styles.input}
                      type="text"
                      name="source"
                      placeholder="Indicação, evento, busca..."
                      value={form.source}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className={styles.ctaRow}>
                  <p className={styles.disclaimer}>
                    Ao solicitar, sua marina entra na fila de análise. Retorno em até 48h via e-mail
                    com as condições do programa e os termos comerciais aplicáveis.
                  </p>
                  {submitError && (
                    <p className="text-red-400 text-xs mb-4">{submitError}</p>
                  )}
                  <button className={styles.btn} onClick={handleSubmit} disabled={submitting}>
                    {submitting ? 'Enviando...' : 'Solicitar Parceria →'}
                  </button>
                </div>
              </>
            ) : (
              <div className={styles.success}>
                <span className={styles.successIcon}>✦</span>
                <h3 className={styles.successTitle}>Solicitação Recebida</h3>
                <p className={styles.successText}>
                  Sua marina entrou na fila fundadora.<br />
                  Você receberá as condições completas em até 48 horas.
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
