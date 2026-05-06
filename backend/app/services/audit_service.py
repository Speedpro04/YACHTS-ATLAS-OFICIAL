"""
Yachts Atlas — Audit Service
Complete tracking system for all actions with maximum detail
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import uuid

from app.core.config import settings
from app.core.supabase import get_supabase_client


logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """All possible audit actions"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    PASSWORD_CHANGE = "password_change"
    
    # Asset Management
    ASSET_CREATE = "asset_create"
    ASSET_UPDATE = "asset_update"
    ASSET_DELETE = "asset_delete"
    ASSET_VIEW = "asset_view"
    
    # Document Management
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_VIEW = "document_view"
    
    # Integrity
    INTEGRITY_VERIFY = "integrity_verify"
    INTEGRITY_REPORT = "integrity_report"
    
    # System
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditService:
    """Premium audit service with complete tracking"""
    
    def __init__(self):
        try:
            self.supabase = get_supabase_client()
            logger.info("AuditService initialized")
        except Exception as e:
            self.supabase = None
            logger.warning(f"AuditService initialized without Supabase client: {str(e)}")
    
    def create_audit_log(
        self,
        action: AuditAction,
        user_id: str,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        error_message: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive audit log entry
        Captures maximum detail for complete traceability
        """
        try:
            audit_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Build comprehensive audit record
            audit_data = {
                "id": audit_id,
                "action": action.value,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": timestamp,
                "severity": severity.value,
                "success": success,
                "details": details or {},
                "error_message": error_message,
                "location": location or {},
                "metadata": metadata or {},
                "created_at": timestamp
            }
            
            # Insert into audit log table
            response = self.supabase.table("audit_logs").insert(audit_data).execute()
            
            if response.data:
                logger.info(f"Audit log created: {action.value} by user {user_id} from {ip_address}")
                return response.data[0]
            else:
                logger.error(f"Failed to create audit log for action: {action.value}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            # Don't raise - audit failures shouldn't break the main flow
            return None
    
    def log_login(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        error_message: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log login attempt with full details"""
        return self.create_audit_log(
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            location=location,
            details={
                "login_type": "standard",
                "timestamp": datetime.utcnow().isoformat()
            },
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING
        )
    
    def log_document_upload(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        document_id: str,
        ativo_id: str,
        file_name: str,
        file_size: int,
        file_hash: str,
        success: bool,
        error_message: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log document upload with complete details"""
        return self.create_audit_log(
            action=AuditAction.DOCUMENT_UPLOAD,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            location=location,
            details={
                "document_id": document_id,
                "ativo_id": ativo_id,
                "file_name": file_name,
                "file_size": file_size,
                "file_hash": file_hash,
                "upload_timestamp": datetime.utcnow().isoformat()
            },
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR
        )
    
    def log_document_download(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        document_id: str,
        ativo_id: str,
        success: bool,
        error_message: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log document download with complete details"""
        return self.create_audit_log(
            action=AuditAction.DOCUMENT_DOWNLOAD,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            location=location,
            details={
                "document_id": document_id,
                "ativo_id": ativo_id,
                "download_timestamp": datetime.utcnow().isoformat()
            },
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING
        )
    
    def log_integrity_verify(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        document_id: str,
        expected_hash: str,
        actual_hash: str,
        is_valid: bool,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log integrity verification with complete details"""
        return self.create_audit_log(
            action=AuditAction.INTEGRITY_VERIFY,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=is_valid,
            location=location,
            details={
                "document_id": document_id,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "integrity_status": "valid" if is_valid else "invalid"
            },
            severity=AuditSeverity.CRITICAL if not is_valid else AuditSeverity.INFO
        )
    
    def log_unauthorized_access(
        self,
        ip_address: str,
        user_agent: str,
        endpoint: str,
        method: str,
        attempted_user_id: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log unauthorized access attempt"""
        return self.create_audit_log(
            action=AuditAction.UNAUTHORIZED_ACCESS,
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            location=location,
            details={
                "endpoint": endpoint,
                "method": method,
                "attempted_user_id": attempted_user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            severity=AuditSeverity.CRITICAL
        )
    
    def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a specific user"""
        try:
            response = self.supabase.table("audit_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            logger.info(f"Retrieved {len(response.data)} audit logs for user {user_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs for user {user_id}: {str(e)}")
            return []
    
    def get_document_audit_logs(
        self,
        document_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a specific document"""
        try:
            response = self.supabase.table("audit_logs")\
                .select("*")\
                .filter("details->>document_id", "eq", document_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            logger.info(f"Retrieved {len(response.data)} audit logs for document {document_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs for document {document_id}: {str(e)}")
            return []
    
    def get_security_events(
        self,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security-related events"""
        try:
            query = self.supabase.table("audit_logs")\
                .select("*")\
                .in_("severity", ["warning", "error", "critical"])\
                .order("timestamp", desc=True)\
                .limit(limit)
            
            if severity:
                query = query.eq("severity", severity.value)
            
            response = query.execute()
            
            logger.info(f"Retrieved {len(response.data)} security events")
            return response.data
            
        except Exception as e:
            logger.error(f"Error retrieving security events: {str(e)}")
            return []
    
    def get_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a user"""
        try:
            from datetime import timedelta
            
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table("audit_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("timestamp", start_date)\
                .execute()
            
            logs = response.data
            
            # Calculate summary
            summary = {
                "total_actions": len(logs),
                "successful_actions": sum(1 for log in logs if log.get("success", False)),
                "failed_actions": sum(1 for log in logs if not log.get("success", False)),
                "unique_ips": len(set(log.get("ip_address") for log in logs)),
                "actions_by_type": {},
                "actions_by_severity": {}
            }
            
            for log in logs:
                action = log.get("action", "unknown")
                severity = log.get("severity", "info")
                
                summary["actions_by_type"][action] = summary["actions_by_type"].get(action, 0) + 1
                summary["actions_by_severity"][severity] = summary["actions_by_severity"].get(severity, 0) + 1
            
            logger.info(f"Generated activity summary for user {user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating activity summary for user {user_id}: {str(e)}")
            return {}


def get_audit_service() -> AuditService:
    """Factory function to get AuditService instance"""
    return AuditService()
