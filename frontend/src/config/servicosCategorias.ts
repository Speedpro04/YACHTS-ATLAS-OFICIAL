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

export type ServicoFieldType = 'text' | 'number' | 'date' | 'time' | 'select' | 'textarea' | 'checkbox'

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
const VID = 'video/mp4,video/quicktime,video/webm,.mov,.qt'

// ── FICHA PADRÃO ────────────────────────────────────────────────────
// Molde único (logbook de aeronave). Elétrica, pintura e
// interior usam esta ficha para registro de serviços gerais.
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

// ── MANUTENÇÃO ESPECIALIZADA ────────────────────────────────────────
// Ficha rica para manutenção náutica: troca de óleo, filtros, Arla 32,
// fluido de arrefecimento, impeller, zincos anódicos e demais consumíveis
// críticos para motores marítimos diesel e gasolina.
const FICHA_MANUTENCAO: ServicoConfig = {
  ctaNovo: 'Registrar Manutenção / Troca de Consumíveis',
  fields: [
    { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Troca de óleo e filtros do motor BB', required: true, full: true },
    { key: 'natureza_manutencao', label: 'Natureza da Manutenção', type: 'select', options: ['Preditiva / Preventiva (Programada)', 'Corretiva (Reparo / Falha)'], required: true },
    { key: 'sistema_afetado', label: 'Sistema Afetado (Norma Náutica)', type: 'select', options: [
      'Propulsão e Linha de Eixo',
      'Geração e Distribuição de Energia (Elétrica/Gerador)',
      'Casco, Estrutura e Apêndices',
      'Faina de Porão (Bombas / Hidráulica)',
      'Salvatagem e Equipamentos de Segurança',
      'Refrigeração e Climatização',
      'Eletrônicos e Navegação',
      'Geral / Outro'
    ], required: true },
    { key: 'tipo_servico', label: 'Ação Técnica / Tipo', type: 'select', options: [
      'Troca de Óleo e Filtros',
      'Troca de Filtros (sem óleo)',
      'Troca de Impeller (Bomba de Água do Mar)',
      'Troca de Zincos Anódicos',
      'Troca de Fluido de Arrefecimento',
      'Revisão Geral / Overhaul',
      'Substituição de Componente',
      'Limpeza / Descarbonização',
      'Outro'
    ], required: true },
    { key: 'status', label: 'Status', type: 'select', options: ['Concluído', 'Pendente', 'Atenção'], required: true },

    { key: 'responsavel', label: 'Responsável / quem executou', type: 'text', placeholder: 'Mecânico ou técnico responsável', required: true },
    { key: 'prestador', label: 'Empresa / oficina / marina', type: 'text', placeholder: 'Oficina, estaleiro, concessionária' },
    { key: 'cnpj', label: 'CNPJ do prestador', type: 'text', placeholder: '00.000.000/0000-00' },

    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'horimetro', label: 'Horímetro na troca', type: 'number', placeholder: 'Leitura no horímetro', required: true, suffix: 'h' },
    { key: 'proxima_troca_horas', label: 'Próxima troca (horímetro)', type: 'number', placeholder: 'Ex: se trocou a 500h e intervalo é 100h → 600', suffix: 'h' },
    { key: 'proxima_revisao', label: 'Próxima revisão (data)', type: 'date' },

    // ── ÓLEO DO MOTOR ──
    { key: 'troca_oleo', label: 'Houve troca de óleo?', type: 'select', options: ['Sim', 'Não'], required: true },
    { key: 'oleo_marca', label: 'Marca do Óleo', type: 'text', placeholder: 'Shell, Mobil, Castrol, Total, Volvo Penta OEM...', showIf: { key: 'troca_oleo', equals: 'Sim' } },
    { key: 'oleo_viscosidade', label: 'Viscosidade / Especificação SAE', type: 'select', options: ['15W-40 (Diesel padrão)', '10W-30', '10W-40', '5W-30', '5W-40', '20W-50', '25W-40 (Marine Diesel)', 'Outro'], showIf: { key: 'troca_oleo', equals: 'Sim' } },
    { key: 'oleo_tipo', label: 'Tipo do Óleo', type: 'select', options: ['Mineral', 'Semi-Sintético', 'Sintético', 'Marine Grade (OEM)'], showIf: { key: 'troca_oleo', equals: 'Sim' } },
    { key: 'oleo_classificacao', label: 'Classificação API', type: 'select', options: ['CI-4 (Diesel)', 'CJ-4 (Diesel Baixa Emissão)', 'CK-4 (Diesel Tier 4)', 'SN (Gasolina)', 'SP (Gasolina)', 'N/A'], showIf: { key: 'troca_oleo', equals: 'Sim' } },
    { key: 'oleo_qtd', label: 'Quantidade de óleo', type: 'number', placeholder: 'Litros utilizados', suffix: 'L', showIf: { key: 'troca_oleo', equals: 'Sim' } },

    // ── FILTROS ──
    { key: 'filtro_oleo', label: 'Filtro de Óleo trocado?', type: 'select', options: ['Sim', 'Não'], required: true },
    { key: 'filtro_oleo_marca', label: 'Marca do Filtro de Óleo', type: 'text', placeholder: 'Mann, Fleetguard, Volvo Penta OEM, Racor...', showIf: { key: 'filtro_oleo', equals: 'Sim' } },
    { key: 'filtro_oleo_pn', label: 'Part Number do Filtro de Óleo', type: 'text', placeholder: 'Ex: 21707134, 3847644', showIf: { key: 'filtro_oleo', equals: 'Sim' } },

    { key: 'filtro_combustivel', label: 'Filtro de Combustível trocado?', type: 'select', options: ['Sim', 'Não'] },
    { key: 'filtro_combustivel_marca', label: 'Marca do Filtro de Combustível', type: 'text', placeholder: 'Racor, Fleetguard, Parker...', showIf: { key: 'filtro_combustivel', equals: 'Sim' } },
    { key: 'filtro_combustivel_pn', label: 'Part Number do Filtro de Combustível', type: 'text', placeholder: 'Ex: 2040TM-OR, R20T', showIf: { key: 'filtro_combustivel', equals: 'Sim' } },

    { key: 'separador_agua', label: 'Separador de Água (Racor) trocado/drenado?', type: 'select', options: ['Trocado', 'Drenado', 'Não'] },
    { key: 'filtro_ar', label: 'Filtro de Ar trocado?', type: 'select', options: ['Sim', 'Não'] },

    // ── ARLA 32 / SCR (Conformidade MARPOL Anexo VI / IMO Tier III) ──
    { key: 'sistema_scr', label: 'Motor possui sistema SCR (Arla 32 / DEF)?', type: 'select', options: ['Sim', 'Não', 'Não sei'] },
    { key: 'scr_conformidade_imo', label: 'Conformidade de Emissões (IMO Tier III / EIAPP)', type: 'select', options: ['Certificado EIAPP Válido (Em conformidade)', 'Não aplicável (Motor isento/antigo)', 'Não conforme / Emissor reprovado'], required: true },
    { key: 'scr_alarme_nox', label: 'Status do Controle de NOx', type: 'select', options: ['Sem alarmes (Operação limpa)', 'Alarme NOx ativado (Falha de emissão)', 'N/A'], showIf: { key: 'sistema_scr', equals: 'Sim' } },
    { key: 'scr_limpeza_injetor', label: 'Manutenção do Injetor de Arla (Descarbonização)', type: 'select', options: ['Injetor Limpo/Descarbonizado nesta O.S.', 'Não realizado', 'Injetor Substituído'], showIf: { key: 'sistema_scr', equals: 'Sim' } },
    { key: 'arla_abastecido', label: 'Arla 32 abastecido nesta manutenção?', type: 'select', options: ['Sim', 'Não'], showIf: { key: 'sistema_scr', equals: 'Sim' } },
    { key: 'arla_qtd', label: 'Quantidade de Arla 32 abastecida', type: 'number', placeholder: 'Litros abastecidos', suffix: 'L', showIf: { key: 'arla_abastecido', equals: 'Sim' } },
    { key: 'arla_marca', label: 'Marca do Arla 32 (Certificação ISO 22241 / Inmetro)', type: 'text', placeholder: 'Ex: BlueMax, BR, original OEM...', showIf: { key: 'arla_abastecido', equals: 'Sim' } },

    // ── ARREFECIMENTO ──
    { key: 'troca_arrefecimento', label: 'Houve troca de fluido de arrefecimento?', type: 'select', options: ['Sim', 'Não'] },
    { key: 'arrefecimento_marca', label: 'Marca do Fluido de Arrefecimento', type: 'text', placeholder: 'Volvo Penta OEM, Prestone, Paraflu...', showIf: { key: 'troca_arrefecimento', equals: 'Sim' } },
    { key: 'arrefecimento_tipo', label: 'Tipo', type: 'select', options: ['Orgânico (OAT)', 'Inorgânico (IAT)', 'Híbrido (HOAT)'], showIf: { key: 'troca_arrefecimento', equals: 'Sim' } },

    // ── IMPELLER (Bomba de Água do Mar) ──
    { key: 'troca_impeller', label: 'Impeller da bomba de água do mar trocado?', type: 'select', options: ['Sim', 'Não'] },
    { key: 'impeller_marca', label: 'Marca / Part Number do Impeller', type: 'text', placeholder: 'Jabsco, Johnson, OEM...', showIf: { key: 'troca_impeller', equals: 'Sim' } },

    // ── ZINCOS ANÓDICOS (Proteção Catódica) ──
    { key: 'troca_zincos', label: 'Zincos anódicos (ânodos de sacrifício) trocados?', type: 'select', options: ['Sim', 'Não'] },
    { key: 'zincos_qtd', label: 'Quantidade de zincos trocados', type: 'number', showIf: { key: 'troca_zincos', equals: 'Sim' } },
    { key: 'zincos_localizacao', label: 'Localização dos zincos', type: 'text', placeholder: 'Eixo, leme, rabeta, casco...', showIf: { key: 'troca_zincos', equals: 'Sim' } },

    // ── CUSTO E OBSERVAÇÕES ──
    { key: 'valor', label: 'Custo total do serviço', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações técnicas', type: 'textarea', placeholder: 'Descreva detalhes da manutenção, condição do óleo drenado (cor, partículas metálicas), estado dos filtros removidos, nível de desgaste dos zincos...', full: true },
  ],
  uploads: [
    { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem — obrigatória quando há valor', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'foto_oleo_drenado', label: 'Foto do óleo drenado', hint: 'Cor e condição do óleo usado (escuro, partículas, leitoso)', accept: IMG, showIf: { key: 'troca_oleo', equals: 'Sim' } },
    { key: 'foto_filtros', label: 'Foto dos filtros trocados (novos e velhos)', hint: 'Comprovação visual dos consumíveis', accept: IMG },
    { key: 'foto_horimetro', label: 'Foto do horímetro no momento da troca', hint: 'Comprovação da leitura', accept: IMG },
    { key: 'fotos_servico', label: 'Fotos adicionais do serviço', hint: 'Até 8 fotos', accept: IMG, multiple: true, max: 8 },
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

// ── MOTOR & PROPULSÃO ────────────────────────────────────────────────
const FICHA_MOTOR: ServicoConfig = {
  ctaNovo: 'Registrar Vistoria / Manutenção de Motor',
  fields: [
    { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Revisão de 100 horas / Repower / Correias', required: true, full: true },
    { key: 'tipo', label: 'Tipo', type: 'select', options: ['Preventiva', 'Corretiva', 'Emergencial', 'Vistoria'], required: true },
    { key: 'status', label: 'Status', type: 'select', options: ['Concluído', 'Pendente', 'Atenção'], required: true },

    { key: 'responsavel', label: 'Responsável / quem executou', type: 'text', placeholder: 'Técnico responsável', required: true },
    { key: 'prestador', label: 'Empresa / prestador / oficina', type: 'text', placeholder: 'Oficina ou concessionária' },
    { key: 'cnpj', label: 'CNPJ do prestador', type: 'text', placeholder: '00.000.000/0000-00' },

    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'concessionaria', label: 'Concessionária autorizada?', type: 'select', options: ['Não', 'Sim'] },
    { key: 'garantia', label: 'Garantia de fábrica vigente até', type: 'date' },

    { key: 'fabricante', label: 'Fabricante do Motor', type: 'text', placeholder: 'Volvo Penta, Yamaha, Mercury, MAN, Yanmar, Cummins...', required: true },
    { key: 'modelo', label: 'Modelo / Linha', type: 'text', placeholder: 'Ex: D6-370 / IPS600', required: true },
    { key: 'numero_serie', label: 'Número de série (gravado no bloco)', type: 'text', placeholder: 'Código de série único do motor', required: true },

    { key: 'ano_fabricacao', label: 'Ano do motor', type: 'number', placeholder: 'Ano de fabricação' },
    { key: 'qtd_motores', label: 'Quantidade de motores', type: 'select', options: ['1 (Single)', '2 (Twin)', '3 (Triple)', '4 (Quadruple)'], required: true },
    { key: 'posicao_motores', label: 'Posição / Montagem', type: 'select', options: ['BB (Bordo)', 'BE (Estibordo)', 'Centro', 'Duplo BB/BE', 'Triplo', 'Quadruplo'] },

    { key: 'tipo_combustivel', label: 'Tipo de combustível', type: 'select', options: ['Diesel', 'Gasolina', 'Elétrico', 'Híbrido'], required: true },
    { key: 'ciclo', label: 'Ciclo', type: 'select', options: ['4 Tempos', '2 Tempos'] },
    { key: 'potencia', label: 'Potência por motor', type: 'number', placeholder: 'Potência', suffix: 'HP' },

    { key: 'transmissao', label: 'Transmissão / Drive', type: 'select', options: ['Inboard Eixo', 'Sterndrive (Rabeta)', 'Pod Drive (IPS/Zeus)', 'Jet Drive', 'Outboard (Popa)'] },
    { key: 'arrefecimento', label: 'Sistema de arrefecimento', type: 'select', options: ['Circuito Fechado (Água Doce)', 'Circuito Aberto (Água do Mar)'] },
    { key: 'tanque_capacidade', label: 'Capacidade do tanque', type: 'number', placeholder: 'Volume do combustível', suffix: 'L' },

    { key: 'horimetro', label: 'Horímetro atual do motor', type: 'number', placeholder: 'Leitura no momento', required: true, suffix: 'h' },
    { key: 'ultima_troca_oleo', label: 'Última troca de óleo (horímetro)', type: 'number', placeholder: 'Leitura no momento da troca', suffix: 'h' },
    { key: 'ultima_revisao', label: 'Última revisão geral / overhaul (horímetro)', type: 'number', placeholder: 'Horímetro do overhaul', suffix: 'h' },

    { key: 'compressao_cilindros', label: 'Compressão por cilindro', type: 'text', placeholder: 'Ex: C1: 150, C2: 152, C3: 150...' },
    { key: 'estado_correias', label: 'Correias, mangueiras e coxins', type: 'select', options: ['Excelente', 'Bom/Operacional', 'Atenção (Trocar)', 'Crítico'] },
    { key: 'estado_exaustao', label: 'Sistema de exaustão / coletores', type: 'select', options: ['Excelente', 'Bom/Operacional', 'Atenção (Carbonizado)', 'Crítico'] },

    { key: 'helice_tipo', label: 'Hélice / Jato (especificação)', type: 'text', placeholder: 'Ex: Passo, diâmetro, pás' },
    { key: 'helice_material', label: 'Material do Hélice', type: 'select', options: ['Bronze', 'Aço Inox', 'Alumínio', 'Composite'] },
    { key: 'helice_estado', label: 'Estado visual (cavitação, amassados)', type: 'select', options: ['Excelente', 'Bom (Leve desgaste)', 'Amassado / Cavitação', 'Crítico'] },

    { key: 'contrato_manutencao', label: 'Contrato de manutenção programada?', type: 'select', options: ['Não', 'Sim'] },
    { key: 'valor', label: 'Custo do serviço / revisão', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações de diagnóstico NDT / detalhes', type: 'textarea', placeholder: 'Pontos críticos, diagnósticos, laudos e observações...', full: true },
  ],
  uploads: [
    { key: 'foto_serie', label: 'Foto do número de série (bloco)', hint: 'Foto obrigatória do número gravado', accept: IMG, required: true },
    { key: 'foto_sala_maquinas', label: 'Foto da sala de máquinas', hint: 'Foto geral nítida da montagem', accept: IMG, required: true },
    { key: 'foto_horimetro', label: 'Foto do horímetro', hint: 'Leitura comprovada no painel', accept: IMG, required: true },
    { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem da NF', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'laudo_analise_oleo', label: 'Laudo de análise de óleo (se houver)', hint: 'Laudo laboratorial em PDF ou JPG', accept: DOC },
    { key: 'laudo_vibracao', label: 'Laudo de vibração / termografia', hint: 'Ensaio técnico NDT em PDF', accept: DOC },
    { key: 'fotos_servico', label: 'Fotos adicionais do motor', hint: 'Até 6 fotos', accept: IMG, multiple: true, max: 6 },
  ]
}

// ── SEGURO & APÓLICE ─────────────────────────────────────────────────
const FICHA_SEGURO: ServicoConfig = {
  ctaNovo: 'Registrar / Atualizar Seguro da Embarcação',
  fields: [
    { key: 'titulo', label: 'Identificação da Apólice', type: 'text', placeholder: 'Ex: Apólice Casco Anual 2026/2027', required: true, full: true },
    { key: 'status', label: 'Status da Apólice', type: 'select', options: ['Vigente', 'Pendente de Renovação', 'Vencida'], required: true },

    { key: 'seguradora', label: 'Seguradora', type: 'text', placeholder: 'Ex: Mapfre, Allianz, Porto Seguro, Tokio Marine...', required: true },
    { key: 'numero_apolice', label: 'Número da Apólice', type: 'text', placeholder: 'Nº do documento de cobertura', required: true },

    { key: 'corretora', label: 'Corretora responsável', type: 'text', placeholder: 'Nome da corretora' },
    { key: 'corretora_cnpj', label: 'CNPJ da Corretora', type: 'text', placeholder: '00.000.000/0000-00' },

    { key: 'vigencia_inicio', label: 'Início da Vigência', type: 'date', required: true },
    { key: 'vigencia_fim', label: 'Fim da Vigência', type: 'date', required: true },
    { key: 'renovacao_automatica', label: 'Renovação automática?', type: 'select', options: ['Não', 'Sim'] },

    { key: 'tipo_cobertura', label: 'Tipo de Cobertura', type: 'select', options: ['Casco (Básica)', 'Responsabilidade Civil (RC)', 'Total / Compreensiva'], required: true },
    { key: 'valor', label: 'Valor Segurado (Valor em Risco)', type: 'number', placeholder: '0,00', suffix: 'R$', required: true },
    { key: 'franquia', label: 'Valor da Franquia / Participação', type: 'text', placeholder: 'Ex: 10% do sinistro, mín R$ 15.000', required: true },

    { key: 'area_navegacao', label: 'Área de navegação coberta', type: 'select', options: ['Costeira', 'Oceânica', 'Fluvial / Interior', 'Internacional'], required: true },
    { key: 'cobertura_anexos', label: 'Cobertura de anexos (tender, jet de apoio)', type: 'text', placeholder: 'Ex: Cobre bote auxiliar até 15HP' },
    { key: 'assistencia_24h', label: 'Assistência 24h incluída?', type: 'select', options: ['Sim', 'Não'] },

    { key: 'alienacao', label: 'Alienação / Beneficiário fiduciário', type: 'text', placeholder: 'Nome do banco (se financiado)' },
    { key: 'status_pagamento', label: 'Status de pagamento do prêmio', type: 'select', options: ['Pago (Quitado)', 'Parcelado em Dia', 'Atrasado'] },
    { key: 'sinistros_historico', label: 'Histórico de sinistros / ocorrências', type: 'textarea', placeholder: 'Liste sinistros passados, datas e valores de franquia acionada...', full: true },
    { key: 'observacao', label: 'Observações / Cláusulas de exclusão críticas', type: 'textarea', placeholder: 'Cláusulas limitantes da apólice...', full: true },
  ],
  uploads: [
    { key: 'apolice_pdf', label: 'Apólice completa (PDF)', hint: 'PDF obrigatório com tabela de coberturas', accept: DOC, required: true },
    { key: 'laudo_vistoria_previa', label: 'Laudo de vistoria prévia da seguradora', hint: 'Laudo técnico pré-requisito (PDF)', accept: DOC },
  ]
}

// ── SEGURANÇA & SALVATAGEM ───────────────────────────────────────────
const FICHA_SEGURANCA: ServicoConfig = {
  ctaNovo: 'Registrar Vistoria de Segurança',
  fields: [
    { key: 'servico', label: 'Descrição da inspeção', type: 'text', placeholder: 'Ex: Vistoria anual de salvatagem NORMAM', required: true, full: true },
    { key: 'status', label: 'Status geral de segurança', type: 'select', options: ['Concluído', 'Pendente', 'Atenção'], required: true },
    { key: 'responsavel', label: 'Responsável técnico / Inspetor', type: 'text', placeholder: 'Nome do inspetor ou empresa credenciada', required: true },
    { key: 'data', label: 'Data da vistoria', type: 'date', required: true },

    { key: 'coletes_validade', label: 'Validade dos Coletes Salva-vidas', type: 'date', required: true },
    { key: 'coletes_qtd', label: 'Quantidade de coletes a bordo', type: 'number', placeholder: 'Qtd de coletes' },
    { key: 'extintor_validade', label: 'Validade da carga do Extintor', type: 'date', required: true },
    { key: 'pirotecnicos_validade', label: 'Validade dos sinalizadores pirotécnicos', type: 'date', required: true },

    // Checklist NORMAM
    { key: 'normam_coletes', label: 'Coletes Homologados', type: 'checkbox', placeholder: 'Coletes em quantidade e classes adequadas para a lotação conforme NORMAM', required: true, full: true },
    { key: 'normam_boia', label: 'Boia Circular com Retinida', type: 'checkbox', placeholder: 'Boias circulares com cabo retinida flutuante sem emendas e em bom estado', required: true, full: true },
    { key: 'normam_sinalizadores', label: 'Sinalizadores Pirotécnicos', type: 'checkbox', placeholder: 'Fogos e pirotécnicos homologados pela DPC e dentro do prazo de validade', required: true, full: true },
    { key: 'normam_extintores', label: 'Extintores de Incêndio', type: 'checkbox', placeholder: 'Extintores portáteis com carga, lacre e validade em dia nos locais corretos', required: true, full: true },
    { key: 'normam_esgotamento', label: 'Esgotamento de Porão', type: 'checkbox', placeholder: 'Bombas de porão manuais e automáticas testadas e operacionais', required: true, full: true },
    { key: 'normam_ancora', label: 'Equipamento de Fundeio (Âncora e Cabos)', type: 'checkbox', placeholder: 'Âncora, amarras e cabos em bom estado e comprimento regulamentar', required: true, full: true },
    { key: 'normam_primeiros_socorros', label: 'Kit de Primeiros Socorros', type: 'checkbox', placeholder: 'Caixa de primeiros socorros abastecida com medicamentos válidos', required: true, full: true },
    { key: 'normam_luzes', label: 'Luzes de Navegação e Sinalização', type: 'checkbox', placeholder: 'Luzes de bordo, alcançado e mastro operacionais para navegação noturna', required: true, full: true },
    { key: 'normam_buzina_sino', label: 'Buzina e Refletor de Radar', type: 'checkbox', placeholder: 'Aparelho de sinalização sonora e refletor de radar instalados e funcionais', required: true, full: true },
    { key: 'normam_radio_vhf', label: 'Rádio VHF/HF e Equipamento de Salvaguarda', type: 'checkbox', placeholder: 'Rádio transceptor homologado com DSC funcional e antenas em ordem', required: true, full: true },

    { key: 'observacao', label: 'Pontos críticos / observações de segurança', type: 'textarea', placeholder: 'Equipamentos vencendo, ausentes ou com avarias...', full: true }
  ],
  uploads: [
    { key: 'foto_extintor_validade', label: 'Foto da etiqueta do extintor', hint: 'Mostrar validade visível', accept: IMG, required: true },
    { key: 'foto_pirotecnicos_validade', label: 'Foto da validade dos sinalizadores', hint: 'Foto da gravação de validade na peça', accept: IMG, required: true },
    { key: 'fotos_salvatagem', label: 'Fotos dos equipamentos de salvatagem', hint: 'Até 6 fotos', accept: IMG, multiple: true, max: 6 }
  ]
}

// ── BOMBAS DE DRENAGEM / PORÃO ──────────────────────────────────────
const FICHA_DRENAGEM: ServicoConfig = {
  ctaNovo: 'Registrar Inspeção de Drenagem / Porão',
  fields: [
    { key: 'servico', label: 'Descrição da Inspeção de Drenagem', type: 'text', placeholder: 'Ex: Teste geral de bombas de porão e alarmes', required: true, full: true },
    { key: 'status', label: 'Status do Sistema', type: 'select', options: ['Excelente', 'Pendente', 'Atenção', 'Crítico'], required: true },
    { key: 'responsavel', label: 'Técnico / Inspetor', type: 'text', placeholder: 'Responsável pelo teste', required: true },
    { key: 'data', label: 'Data do serviço', type: 'date', required: true },

    { key: 'fabricante', label: 'Fabricante da Bomba', type: 'text', placeholder: 'Rule, Johnson Pump, Attwood, Jabsco...', required: true },
    { key: 'modelo', label: 'Modelo da Bomba', type: 'text', placeholder: 'Ex: Rule-Mate 2000 GPH', required: true },
    { key: 'zona', label: 'Zona / Compartimento', type: 'select', options: ['Proa', 'Sala de Máquinas', 'Popa', 'Meio / Cabines', 'Outra'], required: true },
    { key: 'vazao_gph', label: 'Vazão Nominal (GPH)', type: 'number', placeholder: 'Ex: 2000', suffix: 'GPH', required: true },

    { key: 'teste_automatico', label: 'Teste do Automático (Float Switch)', type: 'select', options: ['Operacional', 'Avaria / Falha', 'Não possui automático'], required: true },
    { key: 'alarme_nivel', label: 'Alarme de Nível Alto (High Water Alarm)', type: 'select', options: ['Instalado e Operacional', 'Instalado com Falha', 'Não possui alarme instalado'], required: true },
    { key: 'fiacao_estado', label: 'Estado da Fiação e Conexões elétricas', type: 'select', options: ['Excelente (Estanque)', 'Bom', 'Atenção (Marcas de Oxidação)', 'Crítico (Exposta / Curto)'], required: true },
    { key: 'filtro_estado', label: 'Estado do Filtro / Ralo de Sucção', type: 'select', options: ['Limpo / Desobstruído', 'Necessita Limpeza (Parcialmente obstruído)', 'Obstruído / Danificado'], required: true },

    { key: 'observacao', label: 'Observações de Funcionamento / Teste de Vazão', type: 'textarea', placeholder: 'Descreva em detalhes o tempo de esgotamento, se há retorno de água pela válvula anti-retorno, etc.', full: true }
  ],
  uploads: [
    { key: 'foto_bomba', label: 'Foto da bomba instalada *', hint: 'Mostrar bomba, automático e fiação no porão', accept: IMG, required: true },
    { key: 'video_funcionamento', label: 'Vídeo de funcionamento / teste do automático', hint: 'Vídeo até 3 min (máx 150MB) do teste mecânico do automático', accept: VID }
  ]
}

// ── CASCO & INTEGRIDADE ESTRUTURAL ───────────────────────────────────
const FICHA_CASCO: ServicoConfig = {
  ctaNovo: 'Registrar Inspeção de Casco / Estrutural',
  fields: [
    { key: 'servico', label: 'Serviço ou Vistoria realizada', type: 'text', placeholder: 'Ex: Vistoria de fundo no seco / Inspeção estrutural periódica', required: true, full: true },
    { key: 'status', label: 'Status estrutural do casco', type: 'select', options: ['Excelente', 'Regular / Operacional', 'Atenção (Recomenda-se Reparo)', 'Crítico (Avaria Estrutural)'], required: true },
    { key: 'responsavel', label: 'Inspetor / Engenheiro ou Estaleiro', type: 'text', placeholder: 'Responsável técnico', required: true },

    { key: 'data', label: 'Data da vistoria', type: 'date', required: true },
    { key: 'material_casco', label: 'Material do Casco', type: 'select', options: ['Fibra de Vidro (GRP)', 'Alumínio', 'Aço', 'Carbono', 'Madeira', 'Outro'], required: true },
    { key: 'tipo_construcao', label: 'Tipo de construção', type: 'select', options: ['Monocasco', 'Catamarã (Multicasco)', 'Trimará (Multicasco)'], required: true },

    { key: 'espessura_laminado', label: 'Última medição de espessura de laminado', type: 'text', placeholder: 'Ex: Proa: 18mm, Fundo: 22mm, Costado: 12mm' },
    { key: 'laudo_osmose', label: 'Constatação de Osmose', type: 'select', options: ['Nenhuma constatada', 'Superficial (Bolhas isoladas)', 'Moderada (Tratamento necessário)', 'Severa (Delaminação em andamento)'], required: true },
    { key: 'gelcoat_estado', label: 'Estado visual do Gelcoat', type: 'select', options: ['Excelente', 'Trincas de tensão (aranhas)', 'Trincas estruturais', 'Restaurado'] },

    { key: 'cavernas_reforcos', label: 'Condição das cavernas e anteparas', type: 'select', options: ['Excelente (Íntegro)', 'Sinais de fadiga / trincas', 'Avaria identificada'], required: true },
    { key: 'passagem_casco_seacocks', label: 'Condição de sea-cocks e passagens de casco', type: 'select', options: ['Excelente (Operando suave)', 'Alguns travados ou oxidados', 'Crítico (Vazamento / Oxidação severa)'], required: true },
    { key: 'quilha_estado', label: 'Quilha e leme (fixação e integridade)', type: 'select', options: ['Excelente (Sem folgas)', 'Marcas de impacto', 'Parafusos oxidados / folga na junção', 'N/A (Lancha / Sem quilha)'] },

    { key: 'porao_estado', label: 'Estado geral do porão', type: 'select', options: ['Seco e limpo', 'Presença de água doce', 'Presença de água salgada', 'Presença de óleo / combustível'], required: true },
    { key: 'valor', label: 'Estimativa de custo de reparo estrutural', type: 'number', placeholder: 'Se houver avarias (opcional)', suffix: 'R$' },
    { key: 'observacao', label: 'Observações estruturais detalhadas', type: 'textarea', placeholder: 'Descreva em detalhes o estado estrutural, cavernas, parafusos de quilha e áreas de porão...', full: true }
  ],
  uploads: [
    { key: 'video_estrutura_interna', label: 'Vídeo da Estrutura Interna (Porão/Cavernas) *', hint: 'Vídeo até 3 min (máx 150MB) de porão, cavernas e registros', accept: VID, required: true },
    { key: 'video_sala_maquinas', label: 'Vídeo da Sala de Máquinas (Operacional)', hint: 'Vídeo até 3 min (máx 150MB) em funcionamento', accept: VID },
    { key: 'foto_fundo_externo', label: 'Foto do fundo externo / casco no seco *', hint: 'Foto nítida obrigatória do fundo e quilha', accept: IMG, required: true },
    { key: 'laudo_ultrassom_pdf', label: 'Laudo de ultrassom / espessímetro (PDF)', hint: 'Documento técnico de auditoria estrutural', accept: DOC },
    { key: 'video_quilha_externa', label: 'Vídeo da quilha e leme no seco', hint: 'Vídeo até 3 min (máx 150MB) mostrando folga ou movimento', accept: VID }
  ]
}

// -- SINISTROS & REPAROS ---------------------------------------------
//
// A aba mais grave do sistema era a mais pobre: tinha quatro campos - data,
// evento, reparo, valor - para o assunto que mais pesa numa negociacao e numa
// apolice. E o tema aparecia espalhado em outros dois lugares (avaria no
// Diario de Bordo, "historico de sinistros" como texto livre no Seguro), sem
// nenhum deles ser o lugar de verdade.
//
// POR QUE AQUI, E NAO NA ABA DO CASCO
// Sinistro raramente fica num sistema so. Encalhe atinge casco, helice, eixo e
// leme; incendio na casa de maquinas atinge motor, eletrica e interior;
// alagamento atinge tudo. Uma ficha presa ao casco resolveria justamente o
// caso que, quando acontece de verdade, transborda dele. Por isso os sistemas
// atingidos sao marcaveis em conjunto, e nao uma escolha unica.
//
// E POR QUE O CASCO CONTINUA SIMPLES
// Vistoria de rotina e o uso normal daquela aba: osmose, gelcoat, cavernas,
// espessura. Sem avaria, o gerente preenche a vistoria e pronto. Empurrar
// campos de sinistro para la faria toda vistoria carregar o peso de um evento
// que quase nunca aconteceu.
//
// POR QUE ANTES E DEPOIS
// "Este barco teve um rombo no casco" derruba o valor. "Teve um rombo,
// reparado pelo estaleiro X, com laminacao de Y, laudo anexado e vistoriado"
// preserva - as vezes aumenta, porque prova que a estrutura foi auditada de
// perto. O dossie nao vale por esconder sinistro: vale por provar que ele foi
// resolvido direito. Sem o desfecho, ele so carrega a ma noticia.
//
// SAO DOIS REGISTROS SELADOS, nao um editado depois. A ocorrencia e lacrada
// quando aconteceu; o reparo, quando terminou. Registro selado nao aceita
// alteracao - e e essa trava que da forca ao "antes": ele foi selado quando
// ninguem sabia ainda como ia terminar. O reparo aponta para a ocorrencia
// pelo campo `resolve_id`.
const SIN_OCORRENCIA = { key: 'momento', equals: 'Ocorrencia do sinistro' }
const SIN_REPARO = { key: 'momento', equals: 'Reparo concluido' }
const SIN_SEGURO = { key: 'seguro_acionado', equals: 'Sim' }

const FICHA_SINISTRO: ServicoConfig = {
  ctaNovo: 'Registrar Sinistro ou Reparo',
  fields: [
    { key: 'momento', label: 'O que voce esta registrando', type: 'select', options: [
      'Ocorrencia do sinistro',
      'Reparo concluido'
    ], required: true, full: true },

    // -- A OCORRENCIA -------------------------------------------------
    { key: 'servico', label: 'Resumo do ocorrido', type: 'text', placeholder: 'Ex: Impacto com objeto submerso na proa, bombordo', required: true, full: true },
    { key: 'tipo_sinistro', label: 'Tipo de sinistro', type: 'select', options: [
      'Colisao com outra embarcacao',
      'Impacto com objeto submerso',
      'Encalhe',
      'Choque com estrutura (pier, cais, boia)',
      'Incendio ou principio de incendio',
      'Alagamento / entrada de agua',
      'Afundamento parcial ou total',
      'Temporal / condicoes de mar',
      'Vandalismo, furto ou roubo',
      'Falha estrutural sem impacto',
      'Falha mecanica com dano a outros sistemas',
      'Outro'
    ], required: true, showIf: SIN_OCORRENCIA },
    { key: 'data', label: 'Data da ocorrencia', type: 'date', required: true },
    { key: 'hora', label: 'Hora aproximada', type: 'time', showIf: SIN_OCORRENCIA },
    { key: 'local_ocorrencia', label: 'Local da ocorrencia', type: 'text', placeholder: 'Ex: Canal de acesso, Baia de Ilhabela', full: true, showIf: SIN_OCORRENCIA },
    { key: 'situacao_embarcacao', label: 'A embarcacao estava', type: 'select', options: [
      'Navegando', 'Fundeada', 'Atracada', 'Em marina seca / no seco', 'Sendo rebocada', 'Em transporte terrestre'
    ], showIf: SIN_OCORRENCIA },
    { key: 'responsavel', label: 'Quem reportou / condutor no momento', type: 'text', placeholder: 'Nome de quem estava a bordo ou constatou', required: true },
    { key: 'houve_vitimas', label: 'Houve feridos ou vitimas?', type: 'select', options: ['Nao', 'Sim - sem gravidade', 'Sim - com atendimento medico'], showIf: SIN_OCORRENCIA },
    { key: 'autoridade_acionada', label: 'Autoridade maritima acionada?', type: 'select', options: ['Nao', 'Sim - Capitania dos Portos', 'Sim - Marinha / Salvamento', 'Sim - Bombeiros', 'Sim - Policia'], showIf: SIN_OCORRENCIA },
    { key: 'numero_bo', label: 'Numero do B.O. / protocolo da autoridade', type: 'text', showIf: SIN_OCORRENCIA },

    // -- SISTEMAS ATINGIDOS (marque todos) ----------------------------
    // Caixas independentes, e nao uma escolha unica: sinistro de verdade
    // transborda de um sistema so, e e essa lista que diz ao perito e ao
    // comprador o tamanho real do evento.
    { key: 'sis_casco', label: 'Atingiu: casco / estrutura', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_propulsao', label: 'Atingiu: motor / propulsao', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_governo', label: 'Atingiu: leme, eixo e governo', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_eletrica', label: 'Atingiu: eletrica', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_eletronica', label: 'Atingiu: eletronica / navegacao', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_interior', label: 'Atingiu: interior / acomodacoes', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_conves', label: 'Atingiu: conves e superestrutura', type: 'checkbox', showIf: SIN_OCORRENCIA },
    { key: 'sis_auxiliares', label: 'Atingiu: sistemas auxiliares (bombas, gerador)', type: 'checkbox', showIf: SIN_OCORRENCIA },

    { key: 'extensao_dano', label: 'Extensao do dano', type: 'select', options: [
      'Cosmetico (sem comprometimento)',
      'Atinge o laminado / estrutura superficial',
      'Perfuracao ou dano estrutural localizado',
      'Dano estrutural extenso',
      'Perda total'
    ], required: true, showIf: SIN_OCORRENCIA },
    { key: 'embarcacao_navegavel', label: 'A embarcacao segue navegavel?', type: 'select', options: ['Sim', 'Sim, com restricao', 'Nao - parada ate reparo'], showIf: SIN_OCORRENCIA },
    { key: 'valor', label: 'Estimativa inicial de prejuizo', type: 'number', placeholder: 'Quanto se espera gastar', suffix: 'R$', showIf: SIN_OCORRENCIA },

    // -- SEGURO -------------------------------------------------------
    { key: 'seguro_acionado', label: 'Seguro foi acionado?', type: 'select', options: ['Nao', 'Sim', 'Ainda em analise'], required: true, showIf: SIN_OCORRENCIA },
    { key: 'seguradora', label: 'Seguradora', type: 'text', showIf: SIN_SEGURO },
    { key: 'numero_sinistro', label: 'Numero do sinistro na seguradora', type: 'text', showIf: SIN_SEGURO },
    { key: 'franquia_valor', label: 'Franquia aplicada', type: 'number', suffix: 'R$', showIf: SIN_SEGURO },

    // -- O REPARO -----------------------------------------------------
    { key: 'reparo_estaleiro', label: 'Estaleiro / oficina responsavel', type: 'text', placeholder: 'Quem executou o reparo', full: true, showIf: SIN_REPARO },
    { key: 'reparo_cnpj', label: 'CNPJ do executante', type: 'text', placeholder: '00.000.000/0000-00', showIf: SIN_REPARO },
    { key: 'reparo_inicio', label: 'Inicio do reparo', type: 'date', showIf: SIN_REPARO },
    { key: 'reparo_conclusao', label: 'Conclusao do reparo', type: 'date', showIf: SIN_REPARO },
    { key: 'reparo_descricao', label: 'O que foi feito', type: 'textarea', placeholder: 'Descreva a tecnica, as etapas e os materiais - ex.: enxerto de laminado, 6 camadas de manta 450 e tecido 600 em resina epoxi, refeito o gelcoat', full: true, required: true, showIf: SIN_REPARO },
    { key: 'reparo_pecas', label: 'Pecas ou secoes substituidas', type: 'textarea', placeholder: 'Liste o que foi trocado, com part number quando houver', full: true, showIf: SIN_REPARO },
    { key: 'reparo_valor_real', label: 'Custo real do reparo', type: 'number', placeholder: 'O que foi efetivamente gasto', suffix: 'R$', showIf: SIN_REPARO },
    { key: 'reparo_coberto_seguro', label: 'Coberto pelo seguro?', type: 'select', options: ['Sim, integralmente', 'Sim, parcialmente', 'Nao - custeado pelo proprietario'], showIf: SIN_REPARO },
    { key: 'reparo_aprovado_por', label: 'Vistoriado e aprovado por', type: 'text', placeholder: 'Engenheiro, perito ou inspetor que atestou o reparo', showIf: SIN_REPARO },
    { key: 'status', label: 'Situacao final do ativo', type: 'select', options: [
      'Totalmente reparado - sem ressalva',
      'Reparado com ressalva tecnica',
      'Reparo parcial - pendencias em aberto',
      'Nao reparado'
    ], required: true, showIf: SIN_REPARO },
    { key: 'observacao', label: 'Observacoes', type: 'textarea', placeholder: 'Qualquer detalhe relevante para quem for avaliar este historico no futuro...', full: true }
  ],
  uploads: [
    // O par de fotos e o coracao desta ficha. E a comparacao - mesma proa,
    // mesmo angulo - que transforma "teve um sinistro" em "teve um sinistro e
    // foi resolvido assim".
    { key: 'foto_sinistro', label: 'Fotos do dano (ANTES) *', hint: 'De perto e de longe. GUARDE O ANGULO: a foto do depois precisa ser do mesmo ponto de vista.', accept: IMG, multiple: true, max: 20, requiredIf: { key: 'momento', equals: 'Ocorrencia do sinistro' }, showIf: SIN_OCORRENCIA },
    { key: 'video_sinistro', label: 'Video do dano', hint: 'Video ate 3 min (max 150MB) percorrendo a area atingida', accept: VID, showIf: SIN_OCORRENCIA },
    { key: 'bo_autoridade_pdf', label: 'B.O. ou registro da autoridade (PDF)', hint: 'Capitania, Marinha, Bombeiros ou Policia', accept: DOC, showIf: SIN_OCORRENCIA },
    { key: 'aviso_sinistro_pdf', label: 'Aviso de sinistro a seguradora (PDF)', hint: 'Comprova a data em que a seguradora foi comunicada', accept: DOC, showIf: SIN_SEGURO },

    { key: 'foto_reparo', label: 'Fotos do reparo concluido (DEPOIS) *', hint: 'Mesmo angulo das fotos do antes - e a comparacao que prova o reparo.', accept: IMG, multiple: true, max: 20, requiredIf: { key: 'momento', equals: 'Reparo concluido' }, showIf: SIN_REPARO },
    { key: 'foto_reparo_processo', label: 'Fotos durante o reparo', hint: 'Area aberta, laminacao em andamento, camadas aplicadas - e o que prova COMO foi feito', accept: IMG, multiple: true, max: 30, showIf: SIN_REPARO },
    { key: 'video_reparo', label: 'Video do reparo concluido', hint: 'Video ate 3 min (max 150MB)', accept: VID, showIf: SIN_REPARO },
    { key: 'laudo_reparo_pdf', label: 'Laudo tecnico do reparo (PDF)', hint: 'Ultrassom, espessimetro ou parecer de engenheiro atestando a estrutura', accept: DOC, showIf: SIN_REPARO },
    { key: 'nota_fiscal_reparo', label: 'Nota fiscal do reparo (PDF)', hint: 'Comprova quem executou e quanto custou', accept: DOC, showIf: SIN_REPARO }
  ]
}

// ── SISTEMA ELÉTRICO & ELETRÔNICOS ──────────────────────────────────
const FICHA_ELETRICA: ServicoConfig = {
  ctaNovo: 'Registrar Manutenção Elétrica / Eletrônica',
  fields: [
    // ── IDENTIFICAÇÃO DO SERVIÇO ──────────────────────────────────────
    { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Substituição do banco de baterias de serviço e calibração do VHF DSC', required: true, full: true },
    { key: 'natureza_manutencao', label: 'Natureza da Manutenção', type: 'select', options: [
      'Preditiva / Preventiva (Programada)',
      'Corretiva (Reparo / Falha)'
    ], required: true },
    { key: 'sistema_afetado', label: 'Sistema Elétrico / Eletrônico Afetado (Norma Náutica)', type: 'select', options: [
      'Banco de Baterias (Serviço / Partida / Casa)',
      'Alternadores e Sistema de Carregamento',
      'Painel Elétrico Principal e Disjuntores',
      'Sistema de Distribuição CC (12V / 24V)',
      'Sistema de Distribuição CA (110V / 220V / Shore Power)',
      'Gerador de Bordo',
      'VHF / Rádio DSC (NORMAM — Canal 16)',
      'Sistema AIS (Identificação Automática)',
      'GPS / Ploter / Sonda / Ecobatímetro',
      'EPIRB / PLB (Radiobaliza — ANATEL)',
      'Piloto Automático',
      'Radar de Navegação',
      'Iluminação de Navegação (Lanternas RIPEAM/COLREGS)',
      'Sistema de Monitoramento e Instrumentação',
      'Aterramento e Proteção Galvânica',
      'Geral / Outro'
    ], required: true },
    { key: 'status', label: 'Status após o serviço', type: 'select', options: ['Concluído', 'Pendente', 'Atenção'], required: true },

    { key: 'responsavel', label: 'Responsável / quem executou', type: 'text', placeholder: 'Eletricista náutico ou técnico de eletrônica', required: true },
    { key: 'prestador', label: 'Empresa / prestador', type: 'text', placeholder: 'Empresa instaladora, revendedor autorizado ou marina' },
    { key: 'cnpj', label: 'CNPJ do prestador', type: 'text', placeholder: '00.000.000/0000-00' },
    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'horimetro', label: 'Horímetro do motor na inspeção', type: 'number', placeholder: 'Horímetro', required: true, suffix: 'h' },

    // ── ELÉTRICA DE POTÊNCIA ──────────────────────────────────────────
    { key: 'baterias_tipo', label: 'Tipo das Baterias de Serviço', type: 'select', options: ['Chumbo-Ácido (Inundada)', 'AGM (Absorvida)', 'Gel', 'Lítio (LiFePO4)', 'N/A'] },
    { key: 'baterias_tensao', label: 'Tensão medida no banco de baterias', type: 'number', placeholder: 'Ex: 12.6 ou 25.0', suffix: 'V' },
    { key: 'baterias_capacidade', label: 'Capacidade total do banco', type: 'number', placeholder: 'Ex: 400', suffix: 'Ah' },
    { key: 'baterias_estado', label: 'Estado das Baterias (Laudo de Carga)', type: 'select', options: [
      'Excelente — acima de 80% da capacidade nominal',
      'Bom — 60 a 80% da capacidade',
      'Atenção — 40 a 60% (próximo da troca)',
      'Crítico — abaixo de 40% (substituir imediatamente)'
    ], required: true },
    { key: 'alternador_status', label: 'Status do Alternador Principal', type: 'select', options: ['Carregando corretamente', 'Abaixo da tensão ideal', 'Sem carga (defeituoso)', 'N/A'] },
    { key: 'carregador_bordo', label: 'Carregador de Bateria de Bordo (Shore Power)', type: 'select', options: ['Operacional (Verificado)', 'Com avaria', 'Não instalado', 'N/A'] },

    { key: 'gerador_modelo', label: 'Modelo do Gerador de Bordo', type: 'text', placeholder: 'Ex: Kohler 9EFKOZD / Onan 11.5kW / Yanmar 6kW' },
    { key: 'gerador_horimetro', label: 'Horímetro do Gerador de Bordo', type: 'number', placeholder: 'Horas de uso do gerador', suffix: 'h' },
    { key: 'gerador_status', label: 'Status do Gerador', type: 'select', options: ['Operacional (Testado em carga)', 'Com avaria', 'Não instalado', 'N/A'] },

    { key: 'painel_disjuntores', label: 'Painel Elétrico e Disjuntores', type: 'select', options: ['Todos os disjuntores operacionais', 'Disjuntor(es) com defeito / trocado(s)', 'Curto ou fiação com dano identificado', 'Substituição do painel realizada'], required: true },
    { key: 'isolamento_galvanico', label: 'Isolamento Galvânico / Teste de Fuga de Corrente', type: 'select', options: [
      'Testado — Sem fuga de corrente detectada',
      'Alerta — Pequena fuga (zincos desgastando rápido)',
      'Crítico — Fuga de corrente detectada (Risco galvânico)',
      'Não testado nesta manutenção'
    ], required: true },

    // ── INSTRUMENTAÇÃO E ELETRÔNICOS DE NAVEGAÇÃO (NORMAM) ───────────
    // VHF DSC — Obrigatório por NORMAM-02/DPC em embarcações de esporte e recreio
    { key: 'vhf_dsc_marca', label: 'Marca / Modelo do VHF DSC (Obrigatório — NORMAM-02)', type: 'text', placeholder: 'Ex: ICOM IC-M506 / Standard Horizon GX2200' },
    { key: 'vhf_dsc_mmsi', label: 'MMSI do VHF DSC (Cadastrado Anatel / GMDSS)', type: 'text', placeholder: 'Número MMSI de 9 dígitos (Ex: 710XXXXXX)' },
    { key: 'vhf_dsc_canal16', label: 'Canal 16 monitorado e operacional? (Obrigatório por lei)', type: 'select', options: ['Sim — Canal 16 monitorado e testado', 'Não (Em reparo)', 'VHF sem DSC instalado'], required: true },
    { key: 'vhf_dsc_status', label: 'Status do VHF DSC', type: 'select', options: ['Operacional (Testado)', 'Com avaria', 'Substituído nesta O.S.', 'N/A'] },

    // EPIRB — Radiobaliza (Portaria ANATEL + NORMAM)
    { key: 'epirb_instalada', label: 'EPIRB ou PLB instalada a bordo?', type: 'select', options: ['Sim', 'Não'], required: true },
    { key: 'epirb_marca', label: 'Marca / Modelo da EPIRB', type: 'text', placeholder: 'Ex: McMurdo Smartfind E8 / Kannad SafePro 406', showIf: { key: 'epirb_instalada', equals: 'Sim' } },
    { key: 'epirb_numero_serie', label: 'Número de Série da EPIRB', type: 'text', placeholder: 'Número de série (constante na etiqueta)', showIf: { key: 'epirb_instalada', equals: 'Sim' } },
    { key: 'epirb_validade_bateria', label: 'Validade da Bateria / Próxima Manutenção', type: 'date', showIf: { key: 'epirb_instalada', equals: 'Sim' } },
    { key: 'epirb_anatel', label: 'EPIRB cadastrada na ANATEL (Obrigatório)', type: 'select', options: ['Sim — Cadastro ANATEL vigente', 'Não — Pendente de cadastro (Irregular)', 'Em processo de cadastro'], showIf: { key: 'epirb_instalada', equals: 'Sim' } },

    // AIS — Sistema de Identificação Automática
    { key: 'ais_instalado', label: 'Sistema AIS instalado?', type: 'select', options: ['Sim — Classe B (Recreio)', 'Sim — Classe A (Comercial)', 'Não instalado'], required: true },
    { key: 'ais_mmsi', label: 'MMSI do AIS', type: 'text', placeholder: 'Número MMSI de 9 dígitos', showIf: { key: 'ais_instalado', equals: 'Sim — Classe B (Recreio)' } },
    { key: 'ais_status', label: 'Status do AIS', type: 'select', options: ['Transmitindo e visível no tráfego', 'Com avaria', 'Substituído nesta O.S.'], showIf: { key: 'ais_instalado', equals: 'Sim — Classe B (Recreio)' } },

    // GPS / Ploter / Sonda
    { key: 'gps_ploter_marca', label: 'Marca / Modelo do GPS / Ploter', type: 'text', placeholder: 'Ex: Garmin GPSMAP 8616 / Raymarine Axiom Pro' },
    { key: 'gps_ploter_status', label: 'Status do GPS / Ploter', type: 'select', options: ['Operacional — Cartas atualizadas', 'Operacional — Cartas desatualizadas', 'Com avaria', 'N/A'] },
    { key: 'sonda_ecobatimetro', label: 'Status da Sonda / Ecobatímetro', type: 'select', options: ['Operacional (Leitura de fundo precisa)', 'Com avaria', 'Não instalado'] },
    { key: 'piloto_automatico', label: 'Status do Piloto Automático', type: 'select', options: ['Operacional (Testado em manobra)', 'Com avaria', 'Não instalado'] },
    { key: 'radar_status', label: 'Status do Radar de Navegação', type: 'select', options: ['Operacional (Testado)', 'Com avaria', 'Não instalado'] },

    // Luzes de Navegação — RIPEAM/COLREGS (Regulamento Internacional para Evitar Abalroamentos no Mar)
    { key: 'luzes_navegacao', label: 'Luzes de Navegação (RIPEAM/COLREGS 1972)', type: 'select', options: [
      'Todas conformes — Mastro, Bordo, Popa e Âncora operacionais',
      'Avaria em lanterna de mastro',
      'Avaria em lanterna de bordo (BB/BE)',
      'Avaria em lanterna de popa',
      'Avaria em lanterna de âncora',
      'Múltiplas lanternas com defeito — Não navegável à noite'
    ], required: true },

    // ── VALOR E OBSERVAÇÃO ────────────────────────────────────────────
    { key: 'valor', label: 'Custo total da manutenção / instalação', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações técnicas detalhadas', type: 'textarea', placeholder: 'Descreva o estado do painel 12V/24V/110V/220V, carregadores, inversores, blindagem de cabos, testes de resistência de isolamento (Megôhmetro), condição das conexões...', full: true },
  ],
  uploads: [
    { key: 'nota_fiscal', label: 'Nota fiscal / Ordem de Serviço', hint: 'PDF ou imagem', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'foto_painel', label: 'Foto do Painel Elétrico Principal *', hint: 'Foto nítida dos disjuntores, barramento e etiquetagem', accept: IMG, required: true },
    { key: 'foto_baterias', label: 'Foto do Banco de Baterias', hint: 'Foto mostrando as baterias e conexões', accept: IMG },
    { key: 'foto_epirb', label: 'Foto da EPIRB (com validade visível)', hint: 'Comprova validade da radiobaliza — obrigatório para dossiê com seguradora', accept: IMG },
    { key: 'laudo_eletrico', label: 'Laudo Técnico ou Relatório de Inspeção (PDF)', hint: 'Laudo de isolamento, teste de baterias ou vistoria elétrica', accept: DOC },
  ],
}

// ── MASTREAÇÃO & VELAME ─────────────────────────────────────────────
const FICHA_VELAME: ServicoConfig = {
  ctaNovo: 'Registrar Inspeção de Mastro / Velas',
  fields: [
    { key: 'servico', label: 'Serviço realizado', type: 'text', placeholder: 'Ex: Inspeção de rigging e lavagem de velas', required: true, full: true },
    { key: 'status', label: 'Status estrutural e velas', type: 'select', options: ['Excelente', 'Regular / Operacional', 'Atenção (Substituir/Ajustar)', 'Crítico'], required: true },
    { key: 'responsavel', label: 'Rigger / Velaria responsável', type: 'text', placeholder: 'Nome do rigger ou empresa', required: true },

    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'rigging_idade', label: 'Idade dos cabos de aço / estais', type: 'number', placeholder: 'Anos desde a última troca', suffix: 'anos' },
    { key: 'rigging_inspecao', label: 'Condição dos Estais e Terminais', type: 'select', options: ['Íntegros (Sem trincas/fissuras)', 'Atenção (Sinais de corrosão)', 'Crítico (Substituir cabos/terminais imediatamente)'], required: true },

    { key: 'velas_estado', label: 'Estado das Velas (Mestra / Genoa)', type: 'select', options: ['Excelente (Tecido firme)', 'Regular (Pequenos reparos)', 'Atenção (Costuras fracas / UV desgastado)', 'Crítico (Rasgado / Trocar)'], required: true },
    { key: 'catracas_lubrificacao', label: 'Catracas de bordo lubrificadas?', type: 'select', options: ['Sim, todas lubrificadas', 'Não (Recomenda-se lubrificar)', 'N/A'], required: true },
    { key: 'enrolador_genoa', label: 'Funcionamento do Enrolador de Genoa', type: 'select', options: ['Suave e operacional', 'Pesado / Travando', 'Não possui enrolador', 'N/A'], required: true },

    { key: 'valor', label: 'Custo do serviço', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações de rigging, mastreação e velas', type: 'textarea', placeholder: 'Descreva a tensão dos estais, marcas de desgaste em adriças/escotas, estado do tecido das velas...', full: true },
  ],
  uploads: [
    { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'foto_rigging', label: 'Foto de estais / mastreação *', hint: 'Foto nítida de conexões ou terminais', accept: IMG, required: true },
    { key: 'fotos_velas', label: 'Fotos das velas ou ferragens', hint: 'Até 4 fotos', accept: IMG, multiple: true, max: 4 },
  ],
}

// ── PINTURA & LIMPEZA DE FUNDO ──────────────────────────────────────
const FICHA_PINTURA: ServicoConfig = {
  ctaNovo: 'Registrar Serviço de Pintura / Polimento',
  fields: [
    { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Pintura de fundo e polimento do costado', required: true, full: true },
    { key: 'status', label: 'Status de pintura/polimento', type: 'select', options: ['Excelente', 'Operacional', 'Atenção (Pintura gasta)', 'Crítico (Sem proteção/craca)'], required: true },
    { key: 'responsavel', label: 'Responsável / Pintor', type: 'text', placeholder: 'Nome do responsável', required: true },

    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'tipo_tinta_fundo', label: 'Tipo/Marca da Tinta de Fundo', type: 'text', placeholder: 'Ex: Antifouling Internacional Trilux / Cobre' },
    { key: 'demaos_fundo', label: 'Quantidade de Demãos aplicadas', type: 'number', placeholder: 'Demãos' },

    { key: 'polimento_costado', label: 'Polimento e Vitrificação do Costado?', type: 'select', options: ['Sim, costado completo', 'Apenas gelcoat limpo', 'Não realizado'], required: true },
    { key: 'limpeza_fundo_frequencia', label: 'Limpeza periódica por mergulhador', type: 'text', placeholder: 'Ex: A cada 30 dias / Mensal' },
    { key: 'anodos_sacrificio', label: 'Ânodos de Sacrifício (Zincos)', type: 'select', options: ['Trocados (100% novos)', 'Troca parcial', 'Não trocados (Em bom estado)'], required: true },

    { key: 'valor', label: 'Custo total da pintura/polimento', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações de casco, costado e fundo', type: 'textarea', placeholder: 'Descreva a espessura da tinta antiga, se houve bolhas de osmose tratadas, estado dos eixos/hélices antes da limpeza...', full: true },
  ],
  uploads: [
    { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'foto_seco', label: 'Foto do fundo da embarcação no seco *', hint: 'Foto obrigatória do fundo e quilha antes/depois', accept: IMG, required: true },
    { key: 'fotos_pintura', label: 'Fotos adicionais do serviço', hint: 'Até 6 fotos', accept: IMG, multiple: true, max: 6 },
  ],
}

// ── INTERIOR, CABINES & CONFORTO ────────────────────────────────────
const FICHA_INTERIOR: ServicoConfig = {
  ctaNovo: 'Registrar Manutenção Interna / Conforto',
  fields: [
    { key: 'servico', label: 'Serviço executado', type: 'text', placeholder: 'Ex: Higienização de estofados e revisão do ar condicionado', required: true, full: true },
    { key: 'status', label: 'Status de conservação interna', type: 'select', options: ['Excelente', 'Bom / Operacional', 'Atenção (Pontos de mofo/desgaste)', 'Crítico'], required: true },
    { key: 'responsavel', label: 'Responsável pelo serviço', type: 'text', placeholder: 'Nome do técnico ou marinheiro', required: true },

    { key: 'data', label: 'Data do serviço', type: 'date', required: true },
    { key: 'ar_condicionado_limpeza', label: 'Higienização dos aparelhos de Ar Condicionado', type: 'select', options: ['Sim, filtros e bandejas limpos', 'Não realizado', 'N/A'], required: true },
    { key: 'ar_condicionado_carga', label: 'Carga de Gás e Climatização', type: 'select', options: ['Operando excelente (Gelando)', 'Fraco / Necessita carga', 'N/A'], required: true },

    { key: 'dessalinizador_producao', label: 'Vazão do Dessalinizador', type: 'number', placeholder: 'Capacidade real', suffix: 'L/h' },
    { key: 'dessalinizador_horas', label: 'Horômetro do Dessalinizador', type: 'number', placeholder: 'Horas de uso', suffix: 'h' },

    { key: 'sistema_esgoto_bombas', label: 'Sistemas de Sanitário e Esgoto de Cabine', type: 'select', options: ['Todas as bombas e trituradores OK', 'Alguma bomba com falha', 'Avaria no vaso/sistema', 'N/A'], required: true },
    { key: 'estofados_telas', label: 'Estado das Madeiras e Estofados internos', type: 'select', options: ['Perfeito estado (Sem avarias/mofo)', 'Desgaste natural de uso', 'Recomenda-se reforma/revestimento'], required: true },

    { key: 'valor', label: 'Custo do serviço', type: 'number', placeholder: '0,00', suffix: 'R$' },
    { key: 'observacao', label: 'Observações de cabines, banheiros e cozinha de bordo', type: 'textarea', placeholder: 'Descreva a umidade interna, testes de fluxo do ar condicionado, limpeza das caixas de esgoto...', full: true },
  ],
  uploads: [
    { key: 'nota_fiscal', label: 'Nota fiscal do serviço', hint: 'PDF ou imagem', accept: DOC, requiredIf: { key: 'valor', truthy: true } },
    { key: 'foto_interior', label: 'Foto geral das cabines / salão *', hint: 'Comprovação da organização e higiene', accept: IMG, required: true },
    { key: 'foto_maquinas_conforto', label: 'Foto do ar condicionado / dessalinizador', hint: 'Mostrando os equipamentos vistoriados', accept: IMG },
  ],
}

// ── ABAS TÉCNICAS ───────────────────────────────────────────────────
// Todas as abas técnicas usam a MESMA ficha (idênticas à manutenção).
// Diário de Bordo usa a ficha de operação (FICHA_OPERACAO).
// Fotos e Documentação são tratadas à parte (UploadSecao), por isso
// não entram aqui.
export const SERVICOS: Record<string, ServicoConfig> = {
  manutencao: FICHA_MANUTENCAO,
  operacao: FICHA_OPERACAO,
  seguro: FICHA_SEGURO,
  motor: FICHA_MOTOR,
  casco: FICHA_CASCO,
  sinistros: FICHA_SINISTRO,
  velame: FICHA_VELAME,   // veleiro (substitui "motor")
  eletrica: FICHA_ELETRICA,
  seguranca: FICHA_SEGURANCA,
  drenagem: FICHA_DRENAGEM,
  pintura: FICHA_PINTURA,
  interior: FICHA_INTERIOR,
  dossie: FICHA_PADRAO,
}

export function temFichaRica(categoriaKey: string): boolean {
  return Boolean(SERVICOS[categoriaKey])
}

