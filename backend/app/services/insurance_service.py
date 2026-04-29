"""
Yachts Atlas — Insurance Companies Service
Management for insurance company partners
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum

from app.core.supabase import get_supabase_client
from app.core.config import settings


logger = logging.getLogger(__name__)


class InsuranceStatus(str, Enum):
    """Insurance company status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class InsuranceService:
    """Service for managing insurance company partnerships"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        logger.info("InsuranceService initialized")
    
    def create_insurance_company(
        self,
        name: str,
        cnpj: str,
        email: str,
        phone: str,
        address: str,
        city: str,
        state: str,
        country: str = "BR",
        website: Optional[str] = None,
        logo_url: Optional[str] = None,
        commission_rate: float = 0.10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new insurance company partner"""
        try:
            import uuid
            
            company_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "cnpj": cnpj,
                "email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "website": website,
                "logo_url": logo_url,
                "status": InsuranceStatus.PENDING.value,
                "commission_rate": commission_rate,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("insurance_companies").insert(company_data).execute()
            
            if response.data:
                logger.info(f"Created insurance company: {name}")
                return response.data[0]
            
            raise Exception("Failed to create insurance company")
            
        except Exception as e:
            logger.error(f"Error creating insurance company: {str(e)}")
            raise Exception(f"Failed to create insurance company: {str(e)}")
    
    def get_insurance_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get insurance company by ID"""
        try:
            response = self.supabase.table("insurance_companies").select("*").eq("id", company_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting insurance company: {str(e)}")
            return None
    
    def get_insurance_companies(
        self,
        status: Optional[InsuranceStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all insurance companies"""
        try:
            query = self.supabase.table("insurance_companies").select("*")
            
            if status:
                query = query.eq("status", status.value)
            
            response = query.limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting insurance companies: {str(e)}")
            return []
    
    def update_insurance_company(
        self,
        company_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update insurance company"""
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.supabase.table("insurance_companies").update(updates).eq("id", company_id).execute()
            
            if response.data:
                logger.info(f"Updated insurance company: {company_id}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating insurance company: {str(e)}")
            return None
    
    def activate_insurance_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Activate insurance company"""
        return self.update_insurance_company(company_id, {"status": InsuranceStatus.ACTIVE.value})
    
    def deactivate_insurance_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Deactivate insurance company"""
        return self.update_insurance_company(company_id, {"status": InsuranceStatus.INACTIVE.value})
    
    def generate_api_key(self, company_id: str) -> str:
        """Generate API key for insurance company"""
        try:
            import secrets
            import uuid
            
            api_key = f"ya_ins_{secrets.token_urlsafe(32)}"
            
            self.update_insurance_company(company_id, {"api_key": api_key})
            
            logger.info(f"Generated API key for insurance company: {company_id}")
            return api_key
            
        except Exception as e:
            logger.error(f"Error generating API key: {str(e)}")
            raise Exception(f"Failed to generate API key: {str(e)}")
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return company info"""
        try:
            response = self.supabase.table("insurance_companies").select("*").eq("api_key", api_key).eq("status", InsuranceStatus.ACTIVE.value).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            return None
    
    def get_company_integrations(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all integrations for an insurance company"""
        try:
            response = self.supabase.table("insurance_integrations").select("*").eq("insurance_company_id", company_id).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting company integrations: {str(e)}")
            return []
    
    def verify_dossier_for_insurance(
        self,
        ativo_id: str,
        company_id: str
    ) -> Dict[str, Any]:
        """Verify if dossier meets insurance requirements"""
        try:
            # Get asset documents
            response = self.supabase.table("documentos").select("*").eq("ativo_id", ativo_id).execute()
            
            documents = response.data
            
            # Check if has required documents
            required_docs = ["seguro", "titulo_propriedade", "registro"]
            has_required = all(
                any(doc["tipo"] == req for doc in documents)
                for req in required_docs
            )
            
            # Check if all documents are verified
            all_verified = all(doc["status"] == "verificado" for doc in documents)
            
            result = {
                "ativo_id": ativo_id,
                "company_id": company_id,
                "has_required_documents": has_required,
                "all_documents_verified": all_verified,
                "total_documents": len(documents),
                "verified_documents": sum(1 for doc in documents if doc["status"] == "verificado"),
                "meets_requirements": has_required and all_verified,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Update integration if exists
            integration = self.supabase.table("insurance_integrations").select("*").eq("ativo_id", ativo_id).eq("insurance_company_id", company_id).execute()
            
            if integration.data:
                self.supabase.table("insurance_integrations").update({
                    "dossier_verified": result["meets_requirements"],
                    "dossier_verified_at": result["verified_at"]
                }).eq("id", integration.data[0]["id"]).execute()
            
            logger.info(f"Verified dossier for asset {ativo_id} and company {company_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying dossier: {str(e)}")
            raise Exception(f"Failed to verify dossier: {str(e)}")


def get_insurance_service() -> InsuranceService:
    """Factory function to get InsuranceService instance"""
    return InsuranceService()
