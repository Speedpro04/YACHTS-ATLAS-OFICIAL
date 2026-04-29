from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class BrokerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class DealStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DealType(str, Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    LEASE = "lease"

class InsuranceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class BrokerCreate(BaseModel):
    user_id: str
    company_name: str
    license_number: str
    email: EmailStr
    phone: str
    whatsapp: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "BR"
    website: Optional[str] = None
    logo_url: Optional[str] = None
    commission_rate: float = 0.15

class BrokerUpdate(BaseModel):
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    commission_rate: Optional[float] = None
    status: Optional[BrokerStatus] = None

class DealCreate(BaseModel):
    broker_id: str
    deal_type: DealType
    deal_value: Optional[float] = None
    ativo_id: Optional[str] = None
    seller_id: Optional[str] = None
    buyer_id: Optional[str] = None
    dossier_required: bool = True
    dossier_level: Optional[str] = None
    start_date: Optional[str] = None
    notes: Optional[str] = None

class InsuranceCompanyCreate(BaseModel):
    name: str
    cnpj: str
    email: EmailStr
    phone: str
    address: str
    city: str
    state: str
    country: str = "BR"
    website: Optional[str] = None
    logo_url: Optional[str] = None
    commission_rate: float = 0.10

class InsuranceCompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    commission_rate: Optional[float] = None
    status: Optional[InsuranceStatus] = None
