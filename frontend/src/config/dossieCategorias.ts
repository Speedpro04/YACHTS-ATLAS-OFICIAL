/**
 * Yachts Atlas — Fonte Única de Verdade das Categorias do Dossiê
 * ------------------------------------------------------------------
 * Este arquivo define TODAS as categorias de dados do ativo. Tanto os
 * formulários do sistema quanto o gerador do dossiê leem daqui — assim
 * sistema e dossiê nunca saem de sincronia.
 *
 * Princípios (ver docs/16-mapa-dossie-sistema.md e a memória do projeto):
 *  - Dossiê ÚNICO, sem classes. A categoria aparece se SE APLICA ao ativo.
 *  - "Nenhuma seção vazia": `porteMinimoPes` controla quando a categoria
 *    passa a ser relevante (ex.: Compliance IMO só faz sentido em 80+ pés).
 *  - Custódia, NÃO inspeção: laudos de terceiros são guardados/certificados.
 *  - Uploads recebem metadados de custódia: data, geolocalização, hash SHA-256.
 */

export type FieldType = 'text' | 'number' | 'date' | 'select' | 'textarea'

export interface CategoriaField {
  key: string
  label: string
  type: FieldType
  placeholder?: string
  options?: string[]
  /** Marca campos sensíveis a país (parametrizar p/ LatAm/EUA no futuro) */
  paisEspecifico?: boolean
}

export type Grupo =
  | 'identidade'
  | 'documentacao'
  | 'tecnico'
  | 'laudos'
  | 'visual'
  | 'perfil'
  | 'mercado'
  | 'internacional'

export interface Categoria {
  id: string
  grupo: Grupo
  label: string
  descricao: string
  /** Nome do ícone lucide-react (mapeado na UI) */
  icon: string
  /** Seção correspondente no dossiê (docs/16) */
  dossieSecao: string
  /** A partir de quantos pés a categoria passa a ser relevante (0 = sempre) */
  porteMinimoPes: number
  /** Campos estruturados próprios da categoria */
  campos?: CategoriaField[]
  /** Itens de verificação (marcar como conferido / presente) */
  checklist?: string[]
  /** Aceita upload de documentos/imagens (custódia com hash + geo) */
  uploads?: boolean
  /** Permite múltiplas entradas (ex.: vários motores, vários registros) */
  multiplo?: boolean
}

export const GRUPOS: Record<Grupo, { label: string; ordem: number }> = {
  identidade: { label: 'Identidade', ordem: 1 },
  documentacao: { label: 'Documentação', ordem: 2 },
  tecnico: { label: 'Técnico', ordem: 3 },
  laudos: { label: 'Laudos de Terceiros', ordem: 4 },
  visual: { label: 'Registro Visual', ordem: 5 },
  perfil: { label: 'Perfil do Ativo', ordem: 6 },
  mercado: { label: 'Mercado & Seguro', ordem: 7 },
  internacional: { label: 'Internacional', ordem: 8 },
}

export const CATEGORIAS: Categoria[] = [
  // ── IDENTIDADE ────────────────────────────────────────────────
  {
    id: 'identificacao',
    grupo: 'identidade',
    label: 'Identificação & Registro',
    descricao: 'Dados de identidade e registro da embarcação.',
    icon: 'Anchor',
    dossieSecao: '01 — Identificação',
    porteMinimoPes: 0,
    campos: [
      { key: 'nome', label: 'Nome da Embarcação', type: 'text', placeholder: 'Ex: Aurora III' },
      { key: 'tipo', label: 'Tipo', type: 'select', options: ['Jet Ski', 'Lancha', 'Veleiro', 'Iate', 'Superyacht', 'Outro'] },
      { key: 'fabricante', label: 'Fabricante / Estaleiro', type: 'text', placeholder: 'Ex: Azimut-Benetti' },
      { key: 'modelo', label: 'Modelo', type: 'text', placeholder: 'Ex: Azimut 105' },
      { key: 'ano', label: 'Ano de Fabricação', type: 'number', placeholder: '2019' },
      { key: 'comprimento_pes', label: 'Comprimento (pés)', type: 'number', placeholder: '105' },
      { key: 'boca_m', label: 'Boca (m)', type: 'number' },
      { key: 'calado_m', label: 'Calado (m)', type: 'number' },
      { key: 'arqueacao_gt', label: 'Arqueação Bruta (GT)', type: 'number' },
      { key: 'numero_registro', label: 'Número de Registro', type: 'text', paisEspecifico: true },
      { key: 'bandeira', label: 'Bandeira', type: 'text', paisEspecifico: true },
      { key: 'hin', label: 'HIN (Nº de Casco)', type: 'text' },
      { key: 'mmsi', label: 'MMSI', type: 'text' },
    ],
  },
  {
    id: 'proprietarios',
    grupo: 'identidade',
    label: 'Histórico de Propriedade',
    descricao: 'Cadeia de proprietários e transferências.',
    icon: 'Users',
    dossieSecao: '02 — Histórico de Proprietários',
    porteMinimoPes: 0,
    multiplo: true,
    campos: [
      { key: 'nome', label: 'Proprietário', type: 'text' },
      { key: 'periodo', label: 'Período', type: 'text', placeholder: '2019 – atual' },
      { key: 'tipo', label: 'Transferência', type: 'select', options: ['Proprietário Original', 'Compra e Venda', 'Herança', 'Doação'] },
    ],
  },

  // ── DOCUMENTAÇÃO ──────────────────────────────────────────────
  {
    id: 'documentacao',
    grupo: 'documentacao',
    label: 'Documentação Legal & Fiscal',
    descricao: 'Documentos legais e fiscais — guardados e certificados.',
    icon: 'FileText',
    dossieSecao: '03 — Documentação Legal e Fiscal',
    porteMinimoPes: 0,
    uploads: true,
    checklist: [
      'Certificado de Registro de Embarcação',
      'Certificado de Segurança',
      'Seguro vigente',
      'Habilitação do proprietário',
      'Comprovante de tributos',
      'Nota fiscal / contrato de aquisição',
      'Certidão de ônus / gravames',
    ],
  },

  // ── TÉCNICO ───────────────────────────────────────────────────
  {
    id: 'especificacoes',
    grupo: 'tecnico',
    label: 'Especificações Técnicas',
    descricao: 'Casco, propulsão, capacidades e desempenho.',
    icon: 'Ship',
    dossieSecao: '04 — Especificações Técnicas',
    porteMinimoPes: 0,
    campos: [
      { key: 'material_casco', label: 'Material do Casco', type: 'text', placeholder: 'Fibra / GRP / Alumínio' },
      { key: 'propulsao', label: 'Tipo de Propulsão', type: 'select', options: ['Eixo', 'IPS / Pod', 'Jato', 'Vela', 'Outro'] },
      { key: 'capacidade_combustivel_l', label: 'Combustível (L)', type: 'number' },
      { key: 'capacidade_agua_l', label: 'Água Doce (L)', type: 'number' },
      { key: 'autonomia_nm', label: 'Autonomia (milhas náuticas)', type: 'number' },
      { key: 'velocidade_cruzeiro', label: 'Velocidade Cruzeiro (nós)', type: 'number' },
      { key: 'velocidade_max', label: 'Velocidade Máxima (nós)', type: 'number' },
    ],
  },
  {
    id: 'motorizacao',
    grupo: 'tecnico',
    label: 'Motorização',
    descricao: 'Motores e geradores — o coração mecânico do ativo.',
    icon: 'Gauge',
    dossieSecao: '05 — Motorização',
    porteMinimoPes: 0,
    multiplo: true,
    uploads: true,
    campos: [
      { key: 'fabricante', label: 'Fabricante', type: 'text', placeholder: 'MTU, Volvo Penta, MAN' },
      { key: 'modelo', label: 'Modelo', type: 'text' },
      { key: 'potencia_hp', label: 'Potência (HP)', type: 'number' },
      { key: 'horas', label: 'Horas de Operação', type: 'number' },
      { key: 'numero_serie', label: 'Número de Série', type: 'text' },
    ],
  },
  {
    id: 'sistemas_auxiliares',
    grupo: 'tecnico',
    label: 'Sistemas Auxiliares',
    descricao: 'Estabilizadores, thrusters, ar-condicionado, automação.',
    icon: 'Cpu',
    dossieSecao: '06 — Sistemas Auxiliares',
    porteMinimoPes: 40,
    checklist: [
      'Estabilizadores (Seakeeper / zero speed)',
      'Bow thruster',
      'Stern thruster',
      'Ar-condicionado / AVAC',
      'Geradores',
      'Tratamento de água',
      'Automação de bordo',
    ],
  },
  {
    id: 'manutencao',
    grupo: 'tecnico',
    label: 'Histórico de Manutenção',
    descricao: 'Serviços realizados ao longo do tempo, com comprovantes.',
    icon: 'Wrench',
    dossieSecao: '07 — Histórico de Manutenção',
    porteMinimoPes: 0,
    multiplo: true,
    uploads: true,
    campos: [
      { key: 'data', label: 'Data do Serviço', type: 'date' },
      { key: 'servico', label: 'Serviço Realizado', type: 'text' },
      { key: 'responsavel', label: 'Responsável / Oficina', type: 'text' },
      { key: 'horimetro', label: 'Horímetro na ocasião', type: 'number' },
    ],
  },

  // ── LAUDOS DE TERCEIROS (custódia) ────────────────────────────
  {
    id: 'inspecao_tecnica',
    grupo: 'laudos',
    label: 'Inspeção Técnica',
    descricao: 'Laudo de inspeção emitido por terceiro — guardado e certificado.',
    icon: 'ClipboardCheck',
    dossieSecao: '08 — Inspeção Técnica',
    porteMinimoPes: 46,
    uploads: true,
    campos: [
      { key: 'data', label: 'Data da Inspeção', type: 'date' },
      { key: 'inspetor', label: 'Inspetor / Empresa', type: 'text' },
      { key: 'registro_profissional', label: 'Registro Profissional (CREA/etc.)', type: 'text' },
      { key: 'resumo', label: 'Resumo do Laudo', type: 'textarea' },
    ],
  },
  {
    id: 'auditoria_casco',
    grupo: 'laudos',
    label: 'Auditoria de Casco (END/Ultrassom)',
    descricao: 'Laudo de ensaio não destrutivo do casco — custodiado.',
    icon: 'Waves',
    dossieSecao: '09 — Auditoria Estrutural do Casco',
    porteMinimoPes: 46,
    uploads: true,
    campos: [
      { key: 'data', label: 'Data da Auditoria', type: 'date' },
      { key: 'metodo', label: 'Método', type: 'text', placeholder: 'Ultrassom (UT) — ASNT NDT Level II' },
      { key: 'responsavel', label: 'Responsável Técnico', type: 'text' },
      { key: 'resumo', label: 'Resultado / Observações', type: 'textarea' },
    ],
  },
  {
    id: 'sinistros',
    grupo: 'laudos',
    label: 'Sinistros & Reparos',
    descricao: 'Histórico de ocorrências e reparos, com comprovação.',
    icon: 'AlertTriangle',
    dossieSecao: '10 — Histórico de Sinistros e Reparos',
    porteMinimoPes: 0,
    multiplo: true,
    uploads: true,
    campos: [
      { key: 'data', label: 'Data', type: 'date' },
      { key: 'evento', label: 'Evento', type: 'text' },
      { key: 'reparo', label: 'Reparo Realizado', type: 'text' },
      { key: 'valor_usd', label: 'Valor (USD)', type: 'number' },
    ],
  },

  // ── REGISTRO VISUAL ───────────────────────────────────────────
  {
    id: 'fotografico',
    grupo: 'visual',
    label: 'Registro Fotográfico',
    descricao: 'Imagens do ativo — datadas, geolocalizadas e seladas (SHA-256).',
    icon: 'Camera',
    dossieSecao: '11 — Registro Fotográfico Certificado',
    porteMinimoPes: 0,
    uploads: true,
    checklist: [
      'Vista Lateral (Bombordo)',
      'Vista Lateral (Boreste)',
      'Proa',
      'Popa',
      'Cabine / Interior',
      'Casa de Máquinas',
    ],
  },

  // ── PERFIL DO ATIVO (porte maior) ─────────────────────────────
  {
    id: 'tripulacao',
    grupo: 'perfil',
    label: 'Tripulação',
    descricao: 'Tripulantes e certificações (STCW / MLC).',
    icon: 'Users',
    dossieSecao: '12 — Tripulação',
    porteMinimoPes: 80,
    campos: [
      { key: 'num_tripulantes', label: 'Nº de Tripulantes', type: 'number' },
      { key: 'certificacoes', label: 'Certificações (STCW, etc.)', type: 'textarea' },
    ],
  },
  {
    id: 'tenders_toys',
    grupo: 'perfil',
    label: 'Tenders & Toys',
    descricao: 'Lanchas de apoio, jet skis e equipamentos de lazer.',
    icon: 'Sailboat',
    dossieSecao: '13 — Tenders & Toys',
    porteMinimoPes: 80,
    multiplo: true,
    campos: [
      { key: 'item', label: 'Item', type: 'text', placeholder: 'Tender, jet ski, equipamento de mergulho' },
      { key: 'descricao', label: 'Descrição', type: 'text' },
    ],
  },
  {
    id: 'areas',
    grupo: 'perfil',
    label: 'Áreas & Acomodações',
    descricao: 'Cabines, suítes e áreas premium.',
    icon: 'Armchair',
    dossieSecao: '14 — Áreas & Acomodações',
    porteMinimoPes: 80,
    checklist: [
      'Cabines / Suítes',
      'Heliponto',
      'Beach club',
      'Spa',
      'Elevador',
    ],
  },

  // ── MERCADO & SEGURO ──────────────────────────────────────────
  {
    id: 'avaliacao_mercado',
    grupo: 'mercado',
    label: 'Avaliação de Mercado',
    descricao: 'Laudo de avaliação de valor — custodiado.',
    icon: 'TrendingUp',
    dossieSecao: '15 — Avaliação de Mercado',
    porteMinimoPes: 46,
    uploads: true,
    campos: [
      { key: 'valor_usd', label: 'Valor Estimado (USD)', type: 'number' },
      { key: 'data', label: 'Data da Avaliação', type: 'date' },
      { key: 'fonte', label: 'Fonte / Metodologia', type: 'text' },
    ],
  },
  {
    id: 'relatorio_seguradora',
    grupo: 'mercado',
    label: 'Relatório para Seguradora',
    descricao: 'Dados consolidados para apólice de seguro.',
    icon: 'ShieldCheck',
    dossieSecao: '16 — Relatório para Seguradora',
    porteMinimoPes: 46,
    campos: [
      { key: 'valor_segurado_usd', label: 'Valor Segurado (USD)', type: 'number' },
      { key: 'classe_risco', label: 'Classe de Risco', type: 'select', options: ['Baixo', 'Médio', 'Alto'] },
      { key: 'uso', label: 'Uso Declarado', type: 'text', placeholder: 'Lazer — Costeiro' },
      { key: 'atracacao', label: 'Local de Atracação', type: 'text' },
    ],
  },

  // ── INTERNACIONAL ─────────────────────────────────────────────
  {
    id: 'compliance_imo',
    grupo: 'internacional',
    label: 'Compliance Internacional (IMO)',
    descricao: 'Certificados internacionais — guardados e certificados.',
    icon: 'Globe',
    dossieSecao: '17 — Compliance Internacional (IMO)',
    porteMinimoPes: 80,
    uploads: true,
    campos: [
      { key: 'numero_imo', label: 'Número IMO', type: 'text' },
      { key: 'classe', label: 'Classe de Certificação', type: 'text', placeholder: 'RINA / Bureau Veritas / DNV' },
      { key: 'validade', label: 'Validade do Certificado', type: 'date' },
    ],
    checklist: [
      'SOLAS',
      'ISM Code',
      'ISPS Code',
      'MARPOL',
      'MLC 2006',
      'Certificado de Rádio (ITU)',
    ],
  },
]

/** Retorna apenas as categorias que se aplicam a um ativo de dado porte (em pés). */
export function categoriasParaPorte(comprimentoPes: number): Categoria[] {
  return CATEGORIAS.filter((c) => comprimentoPes >= c.porteMinimoPes)
}

/** Agrupa categorias por grupo, na ordem definida em GRUPOS. */
export function categoriasPorGrupo(cats: Categoria[] = CATEGORIAS) {
  return (Object.keys(GRUPOS) as Grupo[])
    .sort((a, b) => GRUPOS[a].ordem - GRUPOS[b].ordem)
    .map((g) => ({ grupo: g, label: GRUPOS[g].label, categorias: cats.filter((c) => c.grupo === g) }))
    .filter((s) => s.categorias.length > 0)
}
