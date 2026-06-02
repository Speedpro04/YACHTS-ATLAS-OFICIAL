import { useState } from 'react';
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

  const TOTAL_SPOTS = 40;
  const TAKEN_SPOTS = 12; // Atualizar dinamicamente se necessário

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

  const fillPercent = Math.round((TAKEN_SPOTS / TOTAL_SPOTS) * 100);

  return (
    <div className="min-h-screen bg-[#010c20]">
      <Header />
      <div className="pt-[var(--header-h)]">
        <section className={styles.section}>
          <div className={styles.bgGlow} aria-hidden="true" />

          <span className={styles.eyebrow}>Programa de Parceria Exclusiva</span>

          <h2 className={styles.headline}>
            Sua marina.<br />
            <em>Sua receita.</em>
          </h2>

          <p className={styles.subtext}>
            As primeiras marinas a integrar a rede Atlas operam em condições fundadoras — benefícios
            exclusivos que não estarão disponíveis para novos parceiros após o encerramento desta fase.
          </p>

          <div className="mt-8 p-5 border border-[#c5a059]/30 bg-[#c5a059]/5 rounded-sm max-w-3xl mx-auto">
            <p className="text-[#E5D5B7] text-[10px] font-black uppercase tracking-[0.25em] mb-2">
              Clausula Comercial de Dossies
            </p>
            <p className="text-white/70 text-sm leading-relaxed">
              Para parceiros fundadores aprovados: receita de dossies com retencao integral por 18 meses,
              contados da ativacao da conta, conforme instrumento contratual.
            </p>
          </div>

          <div className={styles.spotsRow}>
            <div className={styles.spotsBar}>
              <div className={styles.spotsFill} style={{ width: `${fillPercent}%` }} />
            </div>
            <span className={styles.spotsText}>
              <strong>{TAKEN_SPOTS}</strong> de {TOTAL_SPOTS} vagas ocupadas
            </span>
          </div>

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
                title: 'Acesso Vitalício',
                text: (
                  <>
                    Condições fundadoras são{' '}
                    <strong>permanentes para quem ingressa agora</strong>. O padrão aumenta. O seu custo, não.
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
