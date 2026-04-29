"""
Yachts Atlas — Brokers Service
Management for broker partners
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum

from app.core.supabase import get_supabase_client
from app.core.config import settings


logger = logging.getLogger(__name__)


class BrokerStatus(str, Enum):
    """Broker status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class DealStatus(str, Enum):
    """Deal status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DealType(str, Enum):
    """Deal type"""
    SALE = "sale"
    PURCHASE = "purchase"
    LEASE = "lease"


class BrokerService:
    """Service for managing broker partnerships and deals"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        logger.info("BrokerService initialized")
    
    def create_broker(
        self,
        user_id: str,
        company_name: str,
        license_number: str,
        email: str,
        phone: str,
        whatsapp: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: str = "BR",
        website: Optional[str] = None,
        logo_url: Optional[str] = None,
        commission_rate: float = 0.15,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new broker"""
        try:
            import uuid
            
            broker_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "company_name": company_name,
                "license_number": license_number,
                "email": email,
                "phone": phone,
                "whatsapp": whatsapp,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "website": website,
                "logo_url": logo_url,
                "status": BrokerStatus.PENDING.value,
                "commission_rate": commission_rate,
                "total_deals": 0,
                "total_value": 0,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("brokers").insert(broker_data).execute()
            
            if response.data:
                logger.info(f"Created broker: {company_name}")
                return response.data[0]
            
            raise Exception("Failed to create broker")
            
        except Exception as e:
            logger.error(f"Error creating broker: {str(e)}")
            raise Exception(f"Failed to create broker: {str(e)}")
    
    def get_broker(self, broker_id: str) -> Optional[Dict[str, Any]]:
        """Get broker by ID"""
        try:
            response = self.supabase.table("brokers").select("*").eq("id", broker_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting broker: {str(e)}")
            return None
    
    def get_broker_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get broker by user ID"""
        try:
            response = self.supabase.table("brokers").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting broker by user ID: {str(e)}")
            return None
    
    def get_brokers(
        self,
        status: Optional[BrokerStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all brokers"""
        try:
            query = self.supabase.table("brokers").select("*")
            
            if status:
                query = query.eq("status", status.value)
            
            response = query.limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting brokers: {str(e)}")
            return []
    
    def update_broker(
        self,
        broker_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update broker"""
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.supabase.table("brokers").update(updates).eq("id", broker_id).execute()
            
            if response.data:
                logger.info(f"Updated broker: {broker_id}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating broker: {str(e)}")
            return None
    
    def activate_broker(self, broker_id: str) -> Optional[Dict[str, Any]]:
        """Activate broker"""
        return self.update_broker(broker_id, {"status": BrokerStatus.ACTIVE.value})
    
    def deactivate_broker(self, broker_id: str) -> Optional[Dict[str, Any]]:
        """Deactivate broker"""
        return self.update_broker(broker_id, {"status": BrokerStatus.INACTIVE.value})
    
    def create_deal(
        self,
        broker_id: str,
        deal_type: DealType,
        deal_value: Optional[float] = None,
        ativo_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        dossier_required: bool = True,
        dossier_level: Optional[str] = None,
        start_date: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new deal"""
        try:
            import uuid
            
            # Get broker info for commission
            broker = self.get_broker(broker_id)
            if not broker:
                raise Exception("Broker not found")
            
            commission_rate = broker.get("commission_rate", 0.15)
            commission_amount = deal_value * commission_rate if deal_value else 0
            
            deal_data = {
                "id": str(uuid.uuid4()),
                "broker_id": broker_id,
                "ativo_id": ativo_id,
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "deal_type": deal_type.value,
                "deal_value": deal_value,
                "commission_rate": commission_rate,
                "commission_amount": commission_amount,
                "dossier_required": dossier_required,
                "dossier_level": dossier_level,
                "dossier_purchased": False,
                "status": DealStatus.PENDING.value,
                "start_date": start_date,
                "notes": notes,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table("broker_deals").insert(deal_data).execute()
            
            if response.data:
                logger.info(f"Created deal for broker {broker_id}")
                return response.data[0]
            
            raise Exception("Failed to create deal")
            
        except Exception as e:
            logger.error(f"Error creating deal: {str(e)}")
            raise Exception(f"Failed to create deal: {str(e)}")
    
    def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get deal by ID"""
        try:
            response = self.supabase.table("broker_deals").select("*").eq("id", deal_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting deal: {str(e)}")
            return None
    
    def get_broker_deals(
        self,
        broker_id: str,
        status: Optional[DealStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all deals for a broker"""
        try:
            query = self.supabase.table("broker_deals").select("*").eq("broker_id", broker_id)
            
            if status:
                query = query.eq("status", status.value)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting broker deals: {str(e)}")
            return []
    
    def update_deal(
        self,
        deal_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update deal"""
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.supabase.table("broker_deals").update(updates).eq("id", deal_id).execute()
            
            if response.data:
                logger.info(f"Updated deal: {deal_id}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating deal: {str(e)}")
            return None
    
    def complete_deal(
        self,
        deal_id: str,
        close_date: str
    ) -> Optional[Dict[str, Any]]:
        """Complete deal and update broker stats"""
        try:
            deal = self.get_deal(deal_id)
            if not deal:
                raise Exception("Deal not found")
            
            # Update deal status
            updated_deal = self.update_deal(deal_id, {
                "status": DealStatus.COMPLETED.value,
                "close_date": close_date
            })
            
            if updated_deal:
                # Update broker stats
                broker_id = deal["broker_id"]
                deal_value = deal.get("deal_value", 0)
                
                broker = self.get_broker(broker_id)
                if broker:
                    self.update_broker(broker_id, {
                        "total_deals": broker.get("total_deals", 0) + 1,
                        "total_value": broker.get("total_value", 0) + (deal_value or 0)
                    })
                
                logger.info(f"Completed deal {deal_id}")
                return updated_deal
            
            return None
            
        except Exception as e:
            logger.error(f"Error completing deal: {str(e)}")
            return None
    
    def mark_dossier_purchased(
        self,
        deal_id: str
    ) -> Optional[Dict[str, Any]]:
        """Mark dossier as purchased for a deal"""
        try:
            return self.update_deal(deal_id, {
                "dossier_purchased": True,
                "dossier_purchased_at": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error marking dossier purchased: {str(e)}")
            return None
    
    def get_broker_stats(self, broker_id: str) -> Dict[str, Any]:
        """Get broker statistics"""
        try:
            broker = self.get_broker(broker_id)
            if not broker:
                return {}
            
            deals = self.get_broker_deals(broker_id)
            
            stats = {
                "total_deals": broker.get("total_deals", 0),
                "total_value": broker.get("total_value", 0),
                "active_deals": len([d for d in deals if d["status"] == DealStatus.IN_PROGRESS.value]),
                "completed_deals": len([d for d in deals if d["status"] == DealStatus.COMPLETED.value]),
                "pending_deals": len([d for d in deals if d["status"] == DealStatus.PENDING.value]),
                "dossiers_required": len([d for d in deals if d.get("dossier_required", False)]),
                "dossiers_purchased": len([d for d in deals if d.get("dossier_purchased", False)]),
                "commission_rate": broker.get("commission_rate", 0),
                "total_commission": sum(d.get("commission_amount", 0) for d in deals if d["status"] == DealStatus.COMPLETED.value)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting broker stats: {str(e)}")
            return {}


def get_broker_service() -> BrokerService:
    """Factory function to get BrokerService instance"""
    return BrokerService()
