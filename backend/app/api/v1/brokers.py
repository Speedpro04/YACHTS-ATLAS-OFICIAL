"""
Yachts Atlas — Brokers Endpoints
API for broker partnerships and deals
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.broker_service import BrokerService, BrokerStatus, DealStatus, DealType
from app.schemas.partners import BrokerCreate, BrokerUpdate, DealCreate
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
from app.core.security import verify_token
from typing import Optional

router = APIRouter()
broker_service = BrokerService()
audit_service = AuditService()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.post("/brokers")
async def create_broker(
    broker_in: BrokerCreate,
    request: Request = None
):
    """Create new broker"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        broker = broker_service.create_broker(**broker_in.dict())
        
        # Log broker creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_broker",
                "broker_id": broker["id"],
                "company_name": company_name
            },
            severity=AuditSeverity.INFO
        )
        
        return broker
        
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "action": "create_broker",
                "company_name": company_name
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers")
async def get_brokers(
    status: Optional[BrokerStatus] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get all brokers"""
    try:
        brokers = broker_service.get_brokers(status=status, limit=limit)
        return {"brokers": brokers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}")
async def get_broker(
    broker_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get broker by ID"""
    try:
        broker = broker_service.get_broker(broker_id)
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not found")
        return broker
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/user/{user_id}")
async def get_broker_by_user_id(
    user_id: str,
    request: Request = None
):
    """Get broker by user ID"""
    try:
        broker = broker_service.get_broker_by_user_id(user_id)
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not found")
        return broker
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/brokers/{broker_id}")
async def update_broker(
    broker_id: str,
    updates: BrokerUpdate,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Update broker"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        broker = broker_service.update_broker(broker_id, updates.dict(exclude_unset=True))
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not found")
        
        # Log update
        audit_service.create_audit_log(
            action=AuditAction.ASSET_UPDATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "update_broker",
                "broker_id": broker_id
            },
            severity=AuditSeverity.INFO
        )
        
        return broker
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brokers/{broker_id}/activate")
async def activate_broker(
    broker_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Activate broker"""
    try:
        broker = broker_service.activate_broker(broker_id)
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not found")
        return broker
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brokers/{broker_id}/deactivate")
async def deactivate_broker(
    broker_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Deactivate broker"""
    try:
        broker = broker_service.deactivate_broker(broker_id)
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not found")
        return broker
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals")
async def create_deal(
    deal_in: DealCreate,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Create new deal"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        deal = broker_service.create_deal(**deal_in.dict())
        
        # Log deal creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_deal",
                "deal_id": deal["id"],
                "broker_id": broker_id,
                "deal_type": deal_type.value,
                "deal_value": deal_value
            },
            severity=AuditSeverity.INFO
        )
        
        return deal
        
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "action": "create_deal",
                "broker_id": broker_id,
                "deal_type": deal_type.value
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get deal by ID"""
    try:
        deal = broker_service.get_deal(deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        return deal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}/deals")
async def get_broker_deals(
    broker_id: str,
    status: Optional[DealStatus] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get all deals for a broker"""
    try:
        deals = broker_service.get_broker_deals(broker_id, status=status, limit=limit)
        return {"deals": deals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deals/{deal_id}")
async def update_deal(
    deal_id: str,
    updates: dict,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Update deal"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        deal = broker_service.update_deal(deal_id, updates)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        # Log update
        audit_service.create_audit_log(
            action=AuditAction.ASSET_UPDATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "update_deal",
                "deal_id": deal_id
            },
            severity=AuditSeverity.INFO
        )
        
        return deal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals/{deal_id}/complete")
async def complete_deal(
    deal_id: str,
    close_date: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Complete deal and update broker stats"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        deal = broker_service.complete_deal(deal_id, close_date)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        # Log completion
        audit_service.create_audit_log(
            action=AuditAction.ASSET_UPDATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "complete_deal",
                "deal_id": deal_id,
                "close_date": close_date
            },
            severity=AuditSeverity.INFO
        )
        
        return deal
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals/{deal_id}/dossier-purchased")
async def mark_dossier_purchased(
    deal_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Mark dossier as purchased for a deal"""
    try:
        deal = broker_service.mark_dossier_purchased(deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        return deal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}/stats")
async def get_broker_stats(
    broker_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get broker statistics"""
    try:
        stats = broker_service.get_broker_stats(broker_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))