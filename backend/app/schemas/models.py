from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MARINA_MANAGER = "marina_manager"
    BROKER = "broker"
    INSURANCE_AGENT = "insurance_agent"
    OWNER = "owner"


class TipoAtivo(str, Enum):
    IATE = "iate"
    LANCHA = "lancha"
    VELEIRO = "veleiro"
    JETSKI = "jetski"
    BARCO_PESCA = "barco_pesca"


class Classificacao(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class PorteCategoria(str, Enum):
    COMPACT = "compact"
    EXECUTIVE = "executive"
    SUPERYACHT = "superyacht"


class DossieType(str, Enum):
    VENDA = "venda"
    SEGURADORA = "seguradora"
    ARMADOR = "armador"


# --- Marina Models ---

class MarinaBase(BaseModel):
    name: str
    cnpj: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None


class MarinaCreate(MarinaBase):
    pass


class MarinaResponse(MarinaBase):
    id: str
    subscription_status: str
    subscription_plan: str
    created_at: datetime
    updated_at: datetime


# --- Profile Models ---

class ProfileBase(BaseModel):
    email: EmailStr
    nome: str
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    user_role: UserRole = UserRole.OWNER
    marina_id: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: str
    verified: bool
    created_at: datetime
    updated_at: datetime


# --- Ativo Models ---

class AtivoBase(BaseModel):
    marina_id: str
    owner_id: Optional[str] = None
    tipo: TipoAtivo
    marca: str
    modelo: str
    ano_fabricacao: int
    comprimento_pes: float
    comprimento_metres: Optional[float] = None
    status: str = "ativo"


class AtivoCreate(AtivoBase):
    pass


class AtivoResponse(AtivoBase):
    id: str
    classificacao: Classificacao
    porte_categoria: PorteCategoria
    progresso: int
    created_at: datetime
    updated_at: datetime


# --- Dossie Models ---

class DossieCreate(BaseModel):
    ativo_id: str
    dossie_type: DossieType
    language: str = "pt-BR"


class DossieResponse(BaseModel):
    id: str
    serial_number: str
    ativo_id: str
    marina_id: str
    requested_by: str
    dossie_type: DossieType
    porte_level: PorteCategoria
    language: str
    price_charged: float
    sha256_hash: str
    s3_url: str
    status: str
    expires_at: datetime
    created_at: datetime