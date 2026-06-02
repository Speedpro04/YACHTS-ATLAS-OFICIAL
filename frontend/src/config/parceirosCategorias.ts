/**
 * Yachts Atlas — Categorias do diretório Parceiros Atlas (fonte única).
 * 9 categorias confirmadas, agrupadas. Sem gradiente, sem emoji.
 */

export type GrupoParceiro = 'comercial' | 'operacional' | 'mecanico' | 'reforma'

export interface CategoriaParceiro {
  id: string
  label: string
  descricao: string
  icon: string // nome lucide-react (mapeado na UI)
  grupo: GrupoParceiro
}

export const GRUPOS_PARCEIRO: Record<GrupoParceiro, { label: string; ordem: number }> = {
  comercial: { label: 'Comercial', ordem: 1 },
  operacional: { label: 'Operação & Logística', ordem: 2 },
  mecanico: { label: 'Mecânica', ordem: 3 },
  reforma: { label: 'Reforma & Valorização', ordem: 4 },
}

export const CATEGORIAS_PARCEIRO: CategoriaParceiro[] = [
  { id: 'broker', label: 'Brokers', descricao: 'Corretores de embarcações que vendem com a credibilidade do dossiê.', icon: 'Briefcase', grupo: 'comercial' },
  { id: 'insurance', label: 'Seguros', descricao: 'Seguradoras que precificam com base no histórico verificável.', icon: 'ShieldCheck', grupo: 'comercial' },

  { id: 'tractor', label: 'Tratores & Içamento', descricao: 'Içamento e movimentação de embarcações em marina.', icon: 'Tractor', grupo: 'operacional' },
  { id: 'forklift', label: 'Empilhadeiras', descricao: 'Lançamento e recolhimento em marina seca.', icon: 'Forklift', grupo: 'operacional' },
  { id: 'nautical_transport', label: 'Transporte Náutico', descricao: 'Transporte de embarcações por terra e estrada.', icon: 'Truck', grupo: 'operacional' },
  { id: 'trailer_manufacturer', label: 'Carretas de Transporte', descricao: 'Fabricantes de carretas sob medida por embarcação.', icon: 'Container', grupo: 'operacional' },

  { id: 'outboard_motor', label: 'Motores de Popa', descricao: 'Venda e assistência de motores de popa.', icon: 'Cog', grupo: 'mecanico' },
  { id: 'engine_rebuild', label: 'Retíficas de Motores', descricao: 'Recuperação e reconstrução de motores.', icon: 'Wrench', grupo: 'mecanico' },

  { id: 'refit', label: 'Retrofit & Refit', descricao: 'Reforma e modernização que valorizam o ativo.', icon: 'Hammer', grupo: 'reforma' },
]

export function categoriasParceiroPorGrupo() {
  return (Object.keys(GRUPOS_PARCEIRO) as GrupoParceiro[])
    .sort((a, b) => GRUPOS_PARCEIRO[a].ordem - GRUPOS_PARCEIRO[b].ordem)
    .map((g) => ({
      grupo: g,
      label: GRUPOS_PARCEIRO[g].label,
      categorias: CATEGORIAS_PARCEIRO.filter((c) => c.grupo === g),
    }))
}
