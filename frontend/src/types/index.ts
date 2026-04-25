export interface Usuario {
  id: string
  email: string
  nome: string
  telefone?: string
  whatsapp?: string
  role: string
  created_at: string
}

export interface Ativo {
  id: string
  usuario_id: string
  tipo: 'iate' | 'lancha' | 'veleiro' | 'jetski' | 'barco_pesca'
  marca: string
  modelo: string
  ano_fabricacao: number
  comprimento?: number
  largura?: number
  calado?: number
  material_casco?: string
  capacidade_passageiros?: number
  modelo_motor?: string
  potencia_motor?: number
  num_motores?: number
  tipo_combustivel?: string
  num_cabines?: number
  capacidade_tanque?: number
  nome_reg?: string
  rgp?: string
  vin?: string
  classificacao: 'bronze' | 'silver' | 'gold'
  progresso: number
  status: string
  created_at: string
}

export interface Documento {
  id: string
  ativo_id: string
  usuario_id: string
  nome_arquivo: string
  tipo: string
  categoria: string
  hash_sha256: string
  tamanho_bytes: number
  mime_type: string
  storage_path: string
  uploaded_by: string
  uploaded_at: string
  status: string
  validado_em: string
  hash_anterior?: string
}

export interface Verificacao {
  document_id: string
  hash_original: string
  is_valid: boolean
  storage: string
  verified_at: string
}