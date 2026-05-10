export type DossierTier = 'compact' | 'executive' | 'superyacht';
export type DossierStatus = 'draft' | 'pending_verification' | 'active' | 'archived';
export type InspectionType = 'ultrasound' | 'structural' | 'survey' | 'osmosis';

export interface Dossier {
  id: string;
  marina_id: string;
  owner_id?: string;
  tier: DossierTier;
  status: DossierStatus;
  created_at: string;
  updated_at: string;
}

export interface VesselIdentity {
  id: string;
  dossier_id: string;
  name: string;
  registration_number?: string;
  flag?: string;
  imo_number?: string;
  hull_material?: string;
  year_built?: number;
  created_at: string;
}

export interface EngineSpec {
  manufacturer: string;
  model: string;
  hp: number;
  hours: number;
}

export interface TechnicalSpecs {
  id: string;
  dossier_id: string;
  length_ft: number;
  beam_ft?: number;
  draft_ft?: number;
  engines: EngineSpec[];
  generators: EngineSpec[];
  created_at: string;
}

export interface MaintenanceLog {
  id: string;
  dossier_id: string;
  service_date: string;
  service_type: string;
  description: string;
  performed_by: string;
  verified: boolean;
  created_at: string;
}

export interface TechnicalInspection {
  id: string;
  dossier_id: string;
  inspection_date: string;
  inspection_type: InspectionType;
  inspector_name: string;
  credentials?: string;
  report_url?: string;
  result?: string;
  created_at: string;
}

export interface VaultDocument {
  id: string;
  dossier_id: string;
  document_type: string;
  file_url: string;
  expiry_date?: string;
  created_at: string;
}

// Composite type for the full Dossier payload
export interface FullDigitalDossier extends Dossier {
  identity: VesselIdentity | null;
  technical_specs: TechnicalSpecs | null;
  maintenance_logs: MaintenanceLog[];
  technical_inspections: TechnicalInspection[];
  documents: VaultDocument[];
}
