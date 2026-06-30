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

// ── DIÁRIO DE BORDO ─────────────────────────────────────────────────
// Registro rigoroso de cada IDA AO MAR — a cadeia de custódia completa:
// quem manuseou, quem lançou, quem pilotou (condutor + habilitação),
// quem rebocou de volta, e em que estado retornou. Feito p/ seguradora.
const FICHA_OPERACAO: ServicoConfig = {
  ctaNovo: 'Registrar Ida ao Mar',
  fields: [
    { key: 'data', label: 'Data da operação', type: 'date', required: true },
    { key: 'finalidade', label: 'Finalidade', type: 'select', options: ['Lazer', 'Teste', 'Translado', 'Manutenção', 'Vistoria', 'Outro'], required: true },
    { key: 'local', label: "Local / espelho d'água", type: 'text', placeholder: 'Onde navegou', full: true },

    { key: 'condutor', label: 'Condutor (quem pilotou)', type: 'text', placeholder: 'Nome do condutor', required: true, full: true },
    { key: 'habilitacao', label: 'Habilitação', type: 'select', options: ['Arrais-Amador', 'Mestre-Amador', 'Capitão-Amador', 'Motonauta', 'Profissional', 'Outro'], required: true },
    { key: 'cha_numero', label: 'Nº da CHA', type: 'text', placeholder: 'Carteira de habilitação' },
    { key: 'cha_validade', label: 'Validade da CHA', type: 'date' },
    { key: 'pessoas_bordo', label: 'Pessoas a bordo', type: 'number' },

    { key: 'resp_manuseio', label: 'Responsável pelo manuseio', type: 'text', placeholder: 'Quem preparou / tirou do seco' },
    { key: 'quem_lancou', label: 'Quem lançou na água', type: 'text', placeholder: 'Guincho, rampa, marinheiro' },

    { key: 'hora_saida', label: 'Hora de saída', type: 'time', required: true },
    { key: 'horimetro_saida', label: 'Horímetro na saída', type: 'number', placeholder: 'Leitura ao sair', suffix: 'h', required: true },
    { key: 'hora_retorno', label: 'Hora de retorno', type: 'time', required: true },
    { key: 'horimetro_retorno', label: 'Horímetro no retorno', type: 'number', placeholder: 'Leitura ao voltar', suffix: 'h', required: true },

    { key: 'quem_reboque', label: 'Reboque da água até a marina (quem fez)', type: 'text', placeholder: 'Quem rebocou de volta', full: true },
    { key: 'combustivel', label: 'Combustível no retorno', type: 'select', options: ['Cheio', '3/4', '1/2', '1/4', 'Reserva'] },
    { key: 'condicoes', label: 'Condições de mar / tempo', type: 'text', placeholder: 'Calmo, agitado, vento...' },

    { key: 'retorno_estado', label: 'Retornou sem danos?', type: 'select', options: ['Sim, sem danos', 'Não, com avaria'], required: true, full: true },
    { key: 'avaria_desc', label: 'Descrição da avaria / sinistro', type: 'textarea', placeholder: 'O que ocorreu, extensão do dano...', full: true, showIf: { key: 'retorno_estado', equals: 'Não, com avaria' }, required: true },

    { key: 'observacao', label: 'Observações gerais', type: 'textarea', placeholder: 'Qualquer detalhe relevante da operação', full: true },
  ],
  uploads: [
    { key: 'foto_saida', label: 'Foto na saída (antes)', hint: 'Estado do barco ao sair', accept: IMG },
    { key: 'foto_retorno', label: 'Foto no retorno (depois)', hint: 'Estado ao voltar', accept: IMG },
    { key: 'foto_avaria', label: 'Foto da avaria', hint: 'Obrigatória se retornou com dano', accept: IMG, showIf: { key: 'retorno_estado', equals: 'Não, com avaria' }, requiredIf: { key: 'retorno_estado', equals: 'Não, com avaria' } },
    { key: 'cha_condutor', label: 'CHA / Arrais do condutor', hint: 'Habilitação náutica (PDF ou foto)', accept: DOC },
  ],
}

// ── ABAS TÉCNICAS ───────────────────────────────────────────────────
// Todas as abas técnicas usam a MESMA ficha (idênticas à manutenção).
// Diário de Bordo usa a ficha de operação (FICHA_OPERACAO).
// Fotos e Documentação são tratadas à parte (UploadSecao), por isso
// não entram aqui.
export const SERVICOS: Record<string, ServicoConfig> = {
  manutencao: FICHA_PADRAO,
  operacao: FICHA_OPERACAO,
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
