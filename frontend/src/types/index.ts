export type UserRole = 'admin' | 'marina_manager' | 'broker' | 'insurance_agent' | 'owner';

export interface Usuario {
  id: string;
  email: string;
  nome: string;
  telefone?: string;
  whatsapp?: string;
  user_role: UserRole;
  marina_id?: string;
  verified: boolean;
  created_at: string;
}

export interface Marina {
  id: string;
  name: string;
  cnpj: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  website?: string;
  logo_url?: string;
  subscription_status: 'active' | 'past_due' | 'canceled' | 'trialing';
  subscription_plan: 'marina_basic' | 'marina_pro' | 'marina_enterprise';
  created_at: string;
  updated_at: string;
}

export interface Ativo {
  id: string;
  marina_id: string;
  owner_id?: string;
  tipo: 'iate' | 'lancha' | 'veleiro' | 'jetski' | 'barco_pesca';
  marca: string;
  modelo: string;
  ano_fabricacao: number;
  comprimento_metres?: number;
  comprimento_pes: number;
  classificacao: 'bronze' | 'silver' | 'gold';
  porte_categoria: 'compact' | 'executive' | 'superyacht';
  progresso: number;
  status: 'ativo' | 'inativo' | 'vendido' | 'manutencao';
  created_at: string;
}

export interface Dossie {
  id: string;
  serial_number: string;
  ativo_id: string;
  marina_id: string;
  requested_by: string;
  dossie_type: 'venda' | 'seguradora' | 'armador';
  porte_level: 'compact' | 'executive' | 'superyacht';
  language: string;
  price_charged: number;
  sha256_hash: string;
  s3_url: string;
  status: 'valid' | 'expired' | 'revoked';
  expires_at: string;
  created_at: string;
}