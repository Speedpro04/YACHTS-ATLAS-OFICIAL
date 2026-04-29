"""
Yachts Atlas — Request Tracking Middleware
Captures IP, user agent, location and all request details
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import re

from fastapi import Request, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.audit_service import AuditService, AuditAction, AuditSeverity


logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track all requests with maximum detail
    Captures IP, user agent, location, and all request metadata
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.audit_service = AuditService()
        logger.info("RequestTrackingMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and capture all details"""
        
        # Capture request details
        request_id = self._generate_request_id()
        start_time = datetime.utcnow()
        
        # Extract client information
        client_info = self._extract_client_info(request)
        
        # Log request start
        logger.info(
            f"Request {request_id} started: {request.method} {request.url.path} "
            f"from {client_info['ip_address']} - {client_info['user_agent'][:50]}"
        )
        
        # Add request info to state for use in endpoints
        request.state.request_id = request_id
        request.state.client_info = client_info
        request.state.start_time = start_time
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Add tracking headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
            
            # Log successful request
            logger.info(
                f"Request {request_id} completed: {response.status_code} "
                f"in {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Log error
            logger.error(
                f"Request {request_id} failed after {duration:.3f}s: {str(e)}"
            )
            
            # Log unauthorized access attempts
            if isinstance(e, HTTPException) and e.status_code == 401:
                self.audit_service.log_unauthorized_access(
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    endpoint=str(request.url.path),
                    method=request.method,
                    location=client_info.get('location')
                )
            
            raise
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return f"req_{uuid.uuid4().hex[:16]}"
    
    def _extract_client_info(self, request: Request) -> Dict[str, Any]:
        """
        Extract comprehensive client information from request
        """
        client_info = {
            "ip_address": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
            "referer": request.headers.get("referer", ""),
            "request_method": request.method,
            "request_path": request.url.path,
            "request_query": str(request.url.query) if request.url.query else "",
            "request_scheme": request.url.scheme,
            "request_host": request.url.hostname,
            "request_port": request.url.port,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add location if available
        location = self._get_location_info(client_info['ip_address'])
        if location:
            client_info['location'] = location
        
        # Parse user agent for additional info
        user_agent_info = self._parse_user_agent(client_info['user_agent'])
        client_info['user_agent_info'] = user_agent_info
        
        return client_info
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address with proxy support
        Checks multiple headers for real IP
        """
        # Check various headers for real IP
        ip_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "cf-connecting-ip",  # Cloudflare
            "x-client-ip",
            "forwarded",
        ]
        
        for header in ip_headers:
            ip = request.headers.get(header)
            if ip:
                # x-forwarded-for can contain multiple IPs
                if "," in ip:
                    ip = ip.split(",")[0].strip()
                # Validate IP format
                if self._is_valid_ip(ip):
                    return ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        # Simple IPv4 validation
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        
        # Simple IPv6 validation
        ipv6_pattern = r'^[0-9a-fA-F:]+$'
        if re.match(ipv6_pattern, ip):
            return True
        
        return False
    
    def _get_location_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get location information from IP address
        Note: This is a placeholder - integrate with GeoIP service for production
        """
        if ip_address == "unknown" or ip_address == "127.0.0.1":
            return None
        
        # Placeholder for GeoIP integration
        # In production, integrate with services like:
        # - MaxMind GeoIP2
        # - IPInfo.io
        # - ipstack.com
        
        # For now, return None - location will be added when GeoIP is integrated
        return None
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """
        Parse user agent string for device/browser information
        """
        info = {
            "browser": "unknown",
            "os": "unknown",
            "device": "unknown",
            "is_mobile": False,
            "is_tablet": False,
            "is_desktop": False,
        }
        
        ua_lower = user_agent.lower()
        
        # Detect browser
        if "chrome" in ua_lower and "edge" not in ua_lower:
            info["browser"] = "Chrome"
        elif "firefox" in ua_lower:
            info["browser"] = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            info["browser"] = "Safari"
        elif "edge" in ua_lower:
            info["browser"] = "Edge"
        elif "opera" in ua_lower:
            info["browser"] = "Opera"
        
        # Detect OS
        if "windows" in ua_lower:
            info["os"] = "Windows"
            info["is_desktop"] = True
        elif "mac" in ua_lower:
            info["os"] = "macOS"
            info["is_desktop"] = True
        elif "linux" in ua_lower:
            info["os"] = "Linux"
            info["is_desktop"] = True
        elif "android" in ua_lower:
            info["os"] = "Android"
            info["is_mobile"] = True
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            info["os"] = "iOS"
            if "ipad" in ua_lower:
                info["is_tablet"] = True
            else:
                info["is_mobile"] = True
        
        # Detect device type
        if "mobile" in ua_lower:
            info["device"] = "Mobile"
            info["is_mobile"] = True
        elif "tablet" in ua_lower:
            info["device"] = "Tablet"
            info["is_tablet"] = True
        elif not info["is_mobile"] and not info["is_tablet"]:
            info["device"] = "Desktop"
            info["is_desktop"] = True
        
        return info


def get_client_ip(request: Request) -> str:
    """Helper function to get client IP from request"""
    return request.state.client_info.get("ip_address", "unknown")


def get_user_agent(request: Request) -> str:
    """Helper function to get user agent from request"""
    return request.state.client_info.get("user_agent", "unknown")


def get_client_location(request: Request) -> Optional[Dict[str, Any]]:
    """Helper function to get client location from request"""
    return request.state.client_info.get("location")


def get_request_id(request: Request) -> str:
    """Helper function to get request ID from request"""
    return getattr(request.state, "request_id", "unknown")