"""
Yachts Atlas — Payment Endpoints
Stripe integration for payments and subscriptions
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from app.services.stripe_service import StripeService, PlanType, DossierLevel
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
from app.core.security import verify_token
from typing import Optional

from pydantic import BaseModel
from typing import Optional

router = APIRouter()
stripe_service = StripeService()
audit_service = AuditService()

class OnboardingCheckout(BaseModel):
    email: str
    marina_id: str
    plan_type: PlanType = PlanType.MARINA
    success_url: str
    cancel_url: str

@router.post("/checkout/onboarding")
async def create_onboarding_checkout(
    data: OnboardingCheckout,
    request: Request = None
):
    """Create checkout session for marina onboarding"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        session = stripe_service.create_onboarding_checkout(
            email=data.email,
            marina_id=data.marina_id,
            plan_type=data.plan_type,
            success_url=data.success_url,
            cancel_url=data.cancel_url
        )
        
        # Log checkout creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_onboarding_checkout",
                "marina_id": data.marina_id,
                "plan_type": data.plan_type.value,
                "session_id": session["session_id"]
            },
            severity=AuditSeverity.INFO
        )
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.get("/plans")
async def get_pricing_plans():
    """Get all available pricing plans"""
    try:
        plans = stripe_service.get_pricing_plans()
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout/subscription")
async def create_subscription_checkout(
    plan_type: PlanType,
    success_url: str,
    cancel_url: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Create checkout session for subscription"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        session = stripe_service.create_checkout_session(
            user_id=user_id,
            plan_type=plan_type,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "ip_address": ip_address,
                "user_agent": user_agent[:100] if user_agent else None
            }
        )
        
        # Log checkout creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,  # Using existing action for now
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_subscription_checkout",
                "plan_type": plan_type.value,
                "session_id": session["session_id"],
                "amount": session["amount"]
            },
            severity=AuditSeverity.INFO
        )
        
        return session
        
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
                "action": "create_subscription_checkout",
                "plan_type": plan_type.value
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout/dossier")
async def create_dossier_checkout(
    dossier_level: DossierLevel,
    ativo_id: str,
    success_url: str,
    cancel_url: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Create checkout session for dossier certification with 50/50 split"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        # 1. Look up the asset and its associated marina
        ativo = supabase.table("ativos").select("marina_id").eq("id", ativo_id).execute()
        marina_id = ativo.data[0].get("marina_id") if ativo.data else None
        
        # 2. Look up the marina's Stripe Account ID for the split
        marina_stripe_account = None
        if marina_id:
            marina = supabase.table("marinas").select("stripe_account_id").eq("id", marina_id).execute()
            if marina.data:
                marina_stripe_account = marina.data[0].get("stripe_account_id")
        
        session = stripe_service.create_dossier_checkout_session(
            user_id=user_id,
            dossier_level=dossier_level,
            ativo_id=ativo_id,
            success_url=success_url,
            cancel_url=cancel_url,
            marina_stripe_account_id=marina_stripe_account,
            metadata={
                "ip_address": ip_address,
                "user_agent": user_agent[:100] if user_agent else None,
                "marina_id": marina_id
            }
        )
        
        # Log checkout creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_dossier_checkout",
                "dossier_level": dossier_level.value,
                "ativo_id": ativo_id,
                "session_id": session["session_id"],
                "amount": session["amount"],
                "split_active": bool(marina_stripe_account)
            },
            severity=AuditSeverity.INFO
        )
        
        return session
        
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
                "action": "create_dossier_checkout",
                "dossier_level": dossier_level.value,
                "ativo_id": ativo_id
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        # Read payload
        payload = await request.body()
        
        # Verify webhook signature
        event = stripe_service.verify_webhook_signature(
            payload=payload,
            sig_header=stripe_signature
        )
        
        # Handle event
        result = stripe_service.handle_webhook_event(event)
        
        # Log webhook processing
        audit_service.create_audit_log(
            action=AuditAction.ASSET_UPDATE,  # Using existing action for now
            user_id="system",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "stripe_webhook",
                "event_type": event.type,
                "event_id": event.id,
                "result": result
            },
            severity=AuditSeverity.INFO
        )
        
        return {"status": "success", "event_type": event.type, "result": result}
        
    except Exception as e:
        # Log webhook error
        audit_service.create_audit_log(
            action=AuditAction.SYSTEM_ERROR,
            user_id="system",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "action": "stripe_webhook_error"
            },
            severity=AuditSeverity.CRITICAL
        )
        
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription/{subscription_id}/status")
async def get_subscription_status(
    subscription_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get subscription status"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        status = stripe_service.get_subscription_status(subscription_id)
        
        # Log status check
        audit_service.create_audit_log(
            action=AuditAction.ASSET_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "get_subscription_status",
                "subscription_id": subscription_id,
                "status": status["status"]
            },
            severity=AuditSeverity.INFO
        )
        
        return status
        
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.ASSET_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "action": "get_subscription_status",
                "subscription_id": subscription_id
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = True,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Cancel subscription"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        result = stripe_service.cancel_subscription(subscription_id, at_period_end)
        
        # Log cancellation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_DELETE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "cancel_subscription",
                "subscription_id": subscription_id,
                "at_period_end": at_period_end
            },
            severity=AuditSeverity.INFO
        )
        
        return result
        
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.ASSET_DELETE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "action": "cancel_subscription",
                "subscription_id": subscription_id
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))