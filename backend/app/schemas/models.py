from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


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
    COMPACT = "compact"
    EXECUTIVE = "executive"
    SUPERYACHT = "superyacht"


class MaterialCasco(str, Enum):
    FIBRA = "fibra"
    ALUMINIO = "aluminio"
    MADEIRA = "madeira"
    ACO = "aco"


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str
    nome: str
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nome: str
    telefone: Optional[str]
    whatsapp: Optional[str]
    role: str
    created_at: datetime


class AtivoCreate(BaseModel):
    tipo: TipoAtivo
    marca: str
    modelo: str
    ano_fabricacao: int
    comprimento: Optional[float] = None
    largura: Optional[float] = None
    calado: Optional[float] = None
    material_casco: Optional[MaterialCasco] = None
    capacidade_passageiros: Optional[int] = None
    modelo_motor: Optional[str] = None
    potencia_motor: Optional[int] = None
    num_motores: Optional[int] = None
    tipo_combustivel: Optional[str] = None
    num_cabines: Optional[int] = None
    capacidade_tanque: Optional[int] = None
    nome_reg: Optional[str] = None
    rgp: Optional[str] = None
    vin: Optional[str] = None


class AtivoResponse(BaseModel):
    id: str
    usuario_id: str
    tipo: TipoAtivo
    marca: str
    modelo: str
    ano_fabricacao: int
    classificacao: Classificacao
    progresso: int
    created_at: datetime


class DocumentoUpload(BaseModel):
    ativo_id: str
    tipo: str
    categoria: str
    nome_arquivo: str