"""
Yachts Atlas — Insurance Companies Endpoints
API for insurance company partnerships
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.insurance_service import InsuranceService, InsuranceStatus
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
from app.core.security import verify_token
from typing import Optional

router = APIRouter()
insurance_service = InsuranceService()
audit_service = AuditService()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.post("/companies")
async def create_insurance_company(
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
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Create new insurance company partner"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        company = insurance_service.create_insurance_company(
            name=name,
            cnpj=cnpj,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            country=country,
            website=website,
            logo_url=logo_url,
            commission_rate=commission_rate
        )
        
        # Log company creation
        audit_service.create_audit_log(
            action=AuditAction.ASSET_CREATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "create_insurance_company",
                "company_id": company["id"],
                "company_name": name
            },
            severity=AuditSeverity.INFO
        )
        
        return company
        
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
                "action": "create_insurance_company",
                "company_name": name
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies")
async def get_insurance_companies(
    status: Optional[InsuranceStatus] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get all insurance companies"""
    try:
        companies = insurance_service.get_insurance_companies(status=status, limit=limit)
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}")
async def get_insurance_company(
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get insurance company by ID"""
    try:
        company = insurance_service.get_insurance_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Insurance company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/companies/{company_id}")
async def update_insurance_company(
    company_id: str,
    updates: dict,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Update insurance company"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        company = insurance_service.update_insurance_company(company_id, updates)
        if not company:
            raise HTTPException(status_code=404, detail="Insurance company not found")
        
        # Log update
        audit_service.create_audit_log(
            action=AuditAction.ASSET_UPDATE,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "update_insurance_company",
                "company_id": company_id
            },
            severity=AuditSeverity.INFO
        )
        
        return company
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/companies/{company_id}/activate")
async def activate_insurance_company(
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Activate insurance company"""
    try:
        company = insurance_service.activate_insurance_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Insurance company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/companies/{company_id}/deactivate")
async def deactivate_insurance_company(
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Deactivate insurance company"""
    try:
        company = insurance_service.deactivate_insurance_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Insurance company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/companies/{company_id}/api-key")
async def generate_api_key(
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Generate API key for insurance company"""
    try:
        api_key = insurance_service.generate_api_key(company_id)
        return {"api_key": api_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}/integrations")
async def get_company_integrations(
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Get all integrations for an insurance company"""
    try:
        integrations = insurance_service.get_company_integrations(company_id)
        return {"integrations": integrations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-dossier")
async def verify_dossier_for_insurance(
    ativo_id: str,
    company_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Verify if dossier meets insurance requirements"""
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        result = insurance_service.verify_dossier_for_insurance(ativo_id, company_id)
        
        # Log verification
        audit_service.create_audit_log(
            action=AuditAction.INTEGRITY_VERIFY,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=result["meets_requirements"],
            location=location,
            details={
                "action": "verify_dossier_for_insurance",
                "ativo_id": ativo_id,
                "company_id": company_id,
                "result": result
            },
            severity=AuditSeverity.INFO
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))