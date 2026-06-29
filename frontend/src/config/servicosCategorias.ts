/**
 * Yachts Atlas — Fichas de Serviço (abas técnicas do ativo)
 * ------------------------------------------------------------------
 * Padrão "logbook de aeronave": cada serviço é registrado com rigor —
 * quem fez, quem enviou (automático), horímetro náutico, peça trocada
 * (nova × velha com foto), nota fiscal e valor. Tudo selado (SHA-256) e
 * IMUTÁVEL. Esta config é a fonte única dos campos de cada aba; o
 * SecaoDetalhe (AtivoHub) e o dossiê leem daqui.
 *
 * Fase 1: Manutenção (piloto). Demais abas entram no mesmo molde.
 */

export type ServicoFieldType = 'text' | 'number' | 'date' | 'time' | 'select' | 'textarea'

export interface ServicoField {
  key: string
  label: string
  type: ServicoFieldType
  placeholder?: string
  options?: string[]
  required?: boolean
  /** Só aparece quando outro campo tem o valor indicado */
  showIf?: { key: string; equals: string }
  /** Ocupa a linha inteira do grid */
  full?: boolean
  /** Sufixo visual (ex.: 'h', 'R$') */
  suffix?: string
}

export interface ServicoUploadSlot {
  key: string
  label: string
  hint?: string
  accept?: string
  multiple?: boolean
  max?: number
  /** Obrigatório sempre */
  required?: boolean
  /** Obrigatório quando a condição é satisfeita (trava forte condicional) */
  requiredIf?: { key: string; equals?: string; truthy?: boolean }
  /** Só aparece quando a condição é satisfeita */
  showIf?: { key: string; equals: string }
}

export interface ServicoConfig {
  /** Rótulo do botão de adicionar */
  ctaNovo: string
  /** Campos estruturados da ficha */
  fields: ServicoField[]
  /** Slots de evidência (upload selado) */
  uploads: ServicoUploadSlot[]
}

const DOC = '.pdf,image/png,image/jpeg'
const IMG = 'image/png,image/jpeg'

// ── FICHA PADRÃO ────────────────────────────────────────────────────
// Molde único (logbook de aeronave). TODAS as abas técnicas usam
// exatamente esta ficha — mesmos campos, mesmo rigor, mesmas evidências.
const FICHA_PADRAO: ServicoConfig = {
  ctaNovo: 'Nova Ordem de Serviço',
  fields: [
      { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Revisão dos motores principais', required: true, full: true },
      { key: 'tipo', label: 'Tipo', type: 'select', options: ['Preventiva', 'Corretiva', 'Emergencial', 'Vistoria'], required: true },
      { key: 'status', label: 'Status', type: 'select', options: ['Concluído', 'Pendente', 'Atenção'], required: true },

      { key: 'responsavel', label: 'Responsável / quem executou', type: 'text', placeholder: 'Técnico responsável', required: true },
      { key: 'prestador', label: 'Empresa / prestador', type: 'text', placeholder: 'Oficina, estaleiro, marina' },
      { key: 'cnpj', label: 'CNPJ do prestador', type: 'text', placeholder: '00.000.000/0000-00' },

      { key: 'data', label: 'Data do serviço', type: 'date', required: true },
      { key: 'hora', label: 'Hora', type: 'time' },
      { key: 'local', label: 'Local / oficina', type: 'text', placeholder: 'Onde foi feito' },

      { key: 'horimetro', label: 'Horímetro (horas de motor)', type: 'number', placeholder: 'Leitura no momento', required: true, suffix: 'h' },
      { key: 'horas_trabalhadas', label: 'Horas trabalhadas', type: 'number', suffix: 'h' },
      { key: 'proxima_revisao', label: 'Próxima revisão', type: 'date' },

      { key: 'valor', label: 'Valor do serviço', type: 'number', placeholder: '0,00', suffix: 'R$' },

      { key: 'troca_peca', label: 'Houve troca de peça?', type: 'select', options: ['Não', 'Sim'], required: true },
      { key: 'peca_descricao', label: 'Peça trocada', type: 'text', placeholder: 'Ex: Bomba de água do mar', showIf: { key: 'troca_peca', equals: 'Sim' }, required: true },
      { key: 'peca_part_number', label: 'Part number', type: 'text', showIf: { key: 'troca_peca', equals: 'Sim' } },
      { key: 'peca_serie', label: 'Nº de série (nova)', type: 'text', showIf: { key: 'troca_peca', equals: 'Sim' } },
      { key: 'peca_qtd', label: 'Quantidade', type: 'number', showIf: { key: 'troca_peca', equals: 'Sim' } },

      { key: 'observacao', label: 'Observações', type: 'textarea', placeholder: 'Detalhes, contexto, pontos de atenção...', full: true },
    ],
    uploads: [
      { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem · obrigatória quando há valor', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
      { key: 'peca_nova', label: 'Foto da peça NOVA', hint: 'Obrigatória na troca de peça', accept: IMG, showIf: { key: 'troca_peca', equals: 'Sim' }, requiredIf: { key: 'troca_peca', equals: 'Sim' } },
      { key: 'peca_velha', label: 'Foto da peça VELHA / removida', hint: 'Obrigatória na troca de peça', accept: IMG, showIf: { key: 'troca_peca', equals: 'Sim' }, requiredIf: { key: 'troca_peca', equals: 'Sim' } },
      { key: 'fotos_servico', label: 'Fotos do serviço (antes/depois)', hint: 'Até 12 imagens', accept: IMG, multiple: true, max: 12 },
    ],
}

// ── ABAS TÉCNICAS ───────────────────────────────────────────────────
// Todas as abas usam a MESMA ficha (idênticas à manutenção).
// Fotos e Documentação são tratadas à parte (UploadSecao), por isso
// não entram aqui.
export const SERVICOS: Record<string, ServicoConfig> = {
  manutencao: FICHA_PADRAO,
  seguro: FICHA_PADRAO,
  motor: FICHA_PADRAO,
  velame: FICHA_PADRAO,   // veleiro (substitui "motor")
  eletrica: FICHA_PADRAO,
  seguranca: FICHA_PADRAO,
  pintura: FICHA_PADRAO,
  interior: FICHA_PADRAO,
  dossie: FICHA_PADRAO,
}

export function temFichaRica(categoriaKey: string): boolean {
  return Boolean(SERVICOS[categoriaKey])
}
