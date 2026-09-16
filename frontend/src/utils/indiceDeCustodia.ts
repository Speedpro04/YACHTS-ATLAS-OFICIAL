/**
 * Índice de Custódia — um nome, em todo lugar.
 *
 * POR QUE ESTE ARQUIVO EXISTE (16/09/2026). O mesmo selo aparecia com três
 * grafias: o painel da Marina dizia "Silver", o Portal do Proprietário dizia
 * "PRATA · 80%" e o relatório da frota dizia "silver" numa coluna chamada
 * "Classe", ao lado de outra chamada "Compliance". Dono, Marina e comprador
 * falavam do mesmo número com palavras diferentes — e o comprador, que lê o
 * dossiê e a verificação pública, só conhece "Silver".
 *
 * O nome do grau fica em inglês de propósito, igual ao valor do banco, ao PDF e
 * à página pública de verificação: é nome de selo, não texto corrido.
 *
 * SEM PERCENTUAL AO LADO. O número colado no grau ("Bronze · 100%") foi a
 * confusão que o dossiê já tinha tirado: 100% de quê, se o selo é bronze?
 */

const GRAU: Record<string, string> = {
  gold: 'Gold',
  silver: 'Silver',
  bronze: 'Bronze',
}

/** `silver` -> `Silver`. Valor desconhecido cai em Bronze, como no painel. */
export function rotuloDoIndice(classificacao?: string | null): string {
  return GRAU[(classificacao || '').toLowerCase()] || GRAU.bronze
}

/**
 * Nome do PDF baixado. Antes levava os 8 primeiros caracteres do protocolo —
 * "dossie_azimut_flybridge 64_YA-IATE-.pdf" —, justamente a parte que não
 * identifica o barco, e com espaço no meio. Agora leva o protocolo inteiro,
 * que é o que a verificação pública pede.
 */
export function nomeDoArquivoDoDossie(ativo: { marca?: string; modelo?: string; id: string }): string {
  const limpar = (s?: string) =>
    (s || '').toLowerCase().trim().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  const partes = ['dossie', limpar(ativo.marca), limpar(ativo.modelo), String(ativo.id)].filter(Boolean)
  return `${partes.join('_')}.pdf`
}
