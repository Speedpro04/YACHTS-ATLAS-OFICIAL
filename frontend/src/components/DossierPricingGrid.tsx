import { useState } from 'react';
import styles from './DossierPricingGrid.module.css';
import { X, Shield, Zap } from 'lucide-react';

interface TierProps {
  id: string;
  name: string;
  price: number;
  vessel: string;
  subtitle: string;
  items: string[];
  details: {
    specs: string[];
    compliance: string[];
    technical: { label: string; value: string }[];
  };
  badge?: string;
}

const tiers: TierProps[] = [
  {
    id: 'compact',
    name: 'Compact Dossier',
    price: 200,
    vessel: 'Até 45 Pés',
    subtitle: 'Relatório Essencial de Integridade',
    items: [
      'Histórico de Manutenção',
      'Identidade Técnica do Casco',
      'Galeria de Fotos Certificadas',
      'Selo de Veracidade Atlas'
    ],
    details: {
      technical: [
        { label: 'Validade', value: '12 Meses' },
        { label: 'Blockchain', value: 'SHA-256' },
        { label: 'Nível', value: 'Bronze' },
        { label: 'Suporte', value: 'Digital' }
      ],
      specs: ['Dimensões Básicas', 'Motorização', 'Tanques'],
      compliance: ['Certificado de Propriedade', 'Seguro Base']
    },
    badge: 'Popular'
  },
  {
    id: 'executive',
    name: 'Executive Vault',
    price: 400,
    vessel: '46 a 79 Pés',
    subtitle: 'Auditoria Técnica Profissional',
    items: [
      'Laudo de Ultrassom (END)',
      'Análise de Motores & Fluidos',
      'Compliance de Segurança',
      'Trilha de Auditoria Completa'
    ],
    details: {
      technical: [
        { label: 'Validade', value: '24 Meses' },
        { label: 'Blockchain', value: 'SHA-256' },
        { label: 'Nível', value: 'Silver' },
        { label: 'Suporte', value: 'Prioritário' }
      ],
      specs: ['Sistemas Elétricos', 'Eletrônica de Navegação', 'Geradores'],
      compliance: ['Seguro Premium', 'Histórico de Sinistros', 'Documentação Fiscal']
    }
  },
  {
    id: 'superyacht',
    name: 'Superyacht Sovereign',
    price: 600,
    vessel: 'Acima de 80 Pés',
    subtitle: 'O Padrão Ouro de Governança',
    items: [
      'Relatório Estrutural Completo',
      'Auditoria de Sistemas Críticos',
      'Dossiê de Exportação/Venda',
      'Certificação de Imutabilidade'
    ],
    details: {
      technical: [
        { label: 'Validade', value: 'Vitalícia' },
        { label: 'Blockchain', value: 'SHA-256' },
        { label: 'Nível', value: 'Gold' },
        { label: 'Suporte', value: 'VIP 24/7' }
      ],
      specs: ['Estabilizadores', 'Sistemas Hidráulicos', 'Equipamentos de Segurança'],
      compliance: ['Auditoria Internacional', 'Conformidade de Bandeira', 'Valuation de Mercado']
    },
    badge: 'Exclusive'
  }
];

export default function DossierPricingGrid({ onSelect }: { onSelect: (id: string) => void }) {
  const [activeTier, setActiveTier] = useState<string | null>(null);

  return (
    <div className={styles.wrap}>
      <div className={styles.sectionLabel}>Planos de Certificação</div>
      
      <div className={styles.grid}>
        {tiers.map((tier) => (
          <div 
            key={tier.id} 
            className={`${styles.card} ${activeTier === tier.id ? styles.active : ''}`}
            onClick={() => {
              setActiveTier(activeTier === tier.id ? null : tier.id);
              onSelect(tier.id);
            }}
          >
            {tier.badge && <div className={styles.badge}>{tier.badge}</div>}
            <div className={styles.tier}>{tier.name}</div>
            <div className={styles.price}>US$ {tier.price}</div>
            <div className={styles.vessel}>{tier.vessel}</div>
            
            <div className={styles.title}>{tier.name}</div>
            <div className={styles.subtitle}>{tier.subtitle}</div>
            
            <div className={styles.itemsLabel}>Incluso no Protocolo</div>
            <ul className={styles.items}>
              {tier.items.map((item, i) => (
                <li key={i} className={styles.item}>
                  <span className={styles.dot}></span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {activeTier && (
        <div className={styles.detailPanel}>
          <div className={styles.detailGrid}>
            {tiers.find(t => t.id === activeTier)?.details.technical.map((tech, i) => (
              <div key={i} className={styles.detailBlock}>
                <span className={styles.detailBlockLabel}>{tech.label}</span>
                <span className={styles.detailBlockValue}>{tech.value}</span>
              </div>
            ))}
          </div>

          <div className={styles.detailSections}>
            <div className={styles.detailSection}>
              <div className={styles.detailSectionTitle}>Análise Técnica Detalhada</div>
              {tiers.find(t => t.id === activeTier)?.details.specs.map((spec, i) => (
                <div key={i} className={styles.detailItem}>
                  <Zap size={12} className={styles.detailIcon} />
                  {spec}
                </div>
              ))}
            </div>
            <div className={styles.detailSection}>
              <div className={styles.detailSectionTitle}>Compliance & Certificações</div>
              {tiers.find(t => t.id === activeTier)?.details.compliance.map((comp, i) => (
                <div key={i} className={styles.detailItem}>
                  <Shield size={12} className={styles.detailIcon} />
                  {comp}
                </div>
              ))}
            </div>
          </div>

          <button className={styles.closeBtn} onClick={() => setActiveTier(null)}>
            <X size={12} />
            Fechar Detalhes
          </button>
        </div>
      )}
    </div>
  );
}
