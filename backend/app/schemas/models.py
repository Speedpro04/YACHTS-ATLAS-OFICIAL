from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.core.security import validar_senha


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


# --- Auth Models ---

class UsuarioCreate(BaseModel):
    email: EmailStr
    # Era `Field(min_length=8)` -- um TERCEIRO numero para o mesmo fato (o site
    # exige 10, o Supabase aceita 6). Agora usa a mesma regra de core.security.
    password: str
    nome: str
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None

    @field_validator("password")
    @classmethod
    def _senha_forte(cls, v: str) -> str:
        return validar_senha(v)


class UsuarioResponse(BaseModel):
    id: str
    email: EmailStr
    nome: Optional[str] = None


class MaintenanceLoginRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LeadMarinaCreate(BaseModel):
    marina: str
    name: str
    email: EmailStr
    fleet: str
    # WhatsApp da marina indicada: e por ele que a abordagem sai (Evolution API).
    whatsapp: Optional[str] = None
    source: Optional[str] = None
    # Pagina de onde veio: 'oficial' ou 'lancamento'. Vem do front, entao e
    # tratado como palpite, nao como verdade — o backend valida contra a lista
    # conhecida antes de gravar.
    origem: Optional[str] = None


# --- Ativo Models ---

class AtivoBase(BaseModel):
    marina_id: Optional[str] = None
    owner_id: Optional[str] = None
    tipo: TipoAtivo
    marca: str
    modelo: str
    # NOME da embarcação — o que está pintado na popa e escrito no Título de
    # Inscrição. É o título do dossiê, da página pública de verificação e do
    # Portal do Proprietário: sete telas leem `nome_reg`.
    #
    # A coluna existia no banco e não era declarada aqui nem coletada em lugar
    # nenhum — exatamente o mesmo defeito que largura/calado tiveram, e que o
    # comentário abaixo descreve. Toda embarcação caía no `marca + modelo`, e um
    # dossiê de ativo de alto valor se apresentava como "Marlin Sea Focus" em
    # vez do nome do barco.
    nome_reg: Optional[str] = None
    ano_fabricacao: int
    comprimento_pes: Optional[float] = None
    comprimento_metres: Optional[float] = None
    status: str = "ativo"
    # E-mail do dono da embarcação. É por ele que o armador entra no Portal do
    # Proprietário: digita o e-mail, recebe um código e vê só o que é dele.
    # Sem isto, dar acesso ao dono só seria possível emprestando a conta da
    # marina — e aí ele veria a frota inteira, de todos os clientes dela.
    proprietario_email: Optional[EmailStr] = None
    # WhatsApp do dono. Opcional: sem ele, o código de acesso vai só por
    # e-mail. Com ele, sai pelos dois canais — e para armador brasileiro o
    # WhatsApp costuma chegar antes.
    proprietario_telefone: Optional[str] = None
    # Nome e documento do titular. Diferente dos dois acima, que são CHAVE DE
    # ACESSO: estes são IDENTIDADE, e é o que um dossiê náutico usa para dizer
    # de quem é o barco. Sem eles, o dossiê de um ativo de alto valor mostrava
    # a marina custodiante e nada sobre o dono.
    proprietario_nome: Optional[str] = None
    proprietario_documento: Optional[str] = None

    # Especificações e motorização.
    #
    # As colunas existem no banco desde sempre e NENHUMA era declarada aqui —
    # `create_ativo` fazia getattr("largura") num modelo que não tinha o campo,
    # então lia None e o dado nunca era gravado. Código morto que parecia vivo.
    #
    # São o que um comprador ou uma seguradora procura primeiro: se o barco
    # cabe na vaga (boca), se entra no canal (calado), se atende à apólice
    # (material do casco, motorização) e quanta gente pode levar. Um dossiê de
    # "conformidade náutica" sem isso está incompleto.
    largura: Optional[float] = None                 # boca, em metros
    calado: Optional[float] = None                  # em metros
    material_casco: Optional[str] = None
    capacidade_passageiros: Optional[int] = None
    num_cabines: Optional[int] = None
    # Tipos espelham o BANCO, conferidos em information_schema: largura e
    # calado são numeric; tanque, potência, cabines, motores e passageiros são
    # integer. Declarar potência como texto fazia o Postgres recusar o insert
    # ("invalid input syntax for type integer") — erro que só aparece na hora
    # de gravar, com a marina olhando.
    capacidade_tanque: Optional[int] = None         # litros
    modelo_motor: Optional[str] = None
    potencia_motor: Optional[int] = None            # HP por motor
    num_motores: Optional[int] = None
    tipo_combustivel: Optional[str] = None


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
