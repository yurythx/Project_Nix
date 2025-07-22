"""
Security System
Provides comprehensive security utilities and authentication/authorization
"""
import hashlib
import secrets
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
try:
    import jwt
except ImportError:
    jwt = None
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@dataclass
class SecurityContext:
    """Security context for operations"""
    user: Optional[User] = None
    permissions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ISecurityProvider(ABC):
    """Security provider interface"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user with credentials"""
        pass
    
    @abstractmethod
    def authorize(self, user: User, permission: str) -> bool:
        """Check if user has permission"""
        pass
    
    @abstractmethod
    def generate_token(self, user: User, expires_in: int = 3600) -> str:
        """Generate authentication token"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[User]:
        """Validate authentication token"""
        pass


class SecurityProvider(ISecurityProvider):
    """Security provider implementation"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or getattr(settings, 'SECRET_KEY', 'default-secret-key')
        self.algorithm = 'HS256'
    
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user with credentials"""
        try:
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                return None
            
            user = User.objects.filter(username=username).first()
            if user and user.check_password(password):
                logger.info(f"User {username} authenticated successfully")
                return user
            
            logger.warning(f"Failed authentication attempt for username: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def authorize(self, user: User, permission: str) -> bool:
        """Check if user has permission"""
        try:
            if not user or not user.is_authenticated:
                return False
            
            # Check superuser
            if user.is_superuser:
                return True
            
            # Check user permissions
            if user.has_perm(permission):
                return True
            
            # Check group permissions
            for group in user.groups.all():
                if group.permissions.filter(codename=permission).exists():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return False
    
    def generate_token(self, user: User, expires_in: int = 3600) -> str:
        """Generate JWT authentication token"""
        if jwt is None:
            raise ImportError("PyJWT is required for token generation")
        
        try:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow(),
                'iss': 'django-skeleton'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Generated token for user {user.username}")
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            raise
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT authentication token"""
        if jwt is None:
            logger.warning("PyJWT not available for token validation")
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get('user_id')
            
            if user_id:
                user = User.objects.filter(id=user_id).first()
                if user and user.is_active:
                    logger.debug(f"Token validated for user {user.username}")
                    return user
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None


class PasswordSecurity:
    """Password security utilities"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine password and salt
        combined = password + salt
        
        # Hash using SHA-256
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        expected_hash, _ = PasswordSecurity.hash_password(password, salt)
        return hashed == expected_hash
    
    @staticmethod
    def generate_strong_password(length: int = 12) -> str:
        """Generate a strong password"""
        import string
        
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # Fill remaining length
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            'is_strong': True,
            'score': 0,
            'issues': []
        }
        
        if len(password) < 8:
            result['issues'].append("Password must be at least 8 characters long")
            result['is_strong'] = False
        
        if not re.search(r'[a-z]', password):
            result['issues'].append("Password must contain at least one lowercase letter")
            result['is_strong'] = False
        
        if not re.search(r'[A-Z]', password):
            result['issues'].append("Password must contain at least one uppercase letter")
            result['is_strong'] = False
        
        if not re.search(r'\d', password):
            result['issues'].append("Password must contain at least one digit")
            result['is_strong'] = False
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append("Password must contain at least one special character")
            result['is_strong'] = False
        
        # Calculate score
        result['score'] = len(password) * 2
        if re.search(r'[a-z]', password):
            result['score'] += 10
        if re.search(r'[A-Z]', password):
            result['score'] += 10
        if re.search(r'\d', password):
            result['score'] += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['score'] += 10
        
        return result


class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content"""
        import html
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove potentially dangerous HTML tags
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input']
        for tag in dangerous_tags:
            text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(f'<{tag}[^>]*/>', '', text, flags=re.IGNORECASE)
        
        # Remove dangerous attributes
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'javascript:']
        for attr in dangerous_attrs:
            text = re.sub(f'{attr}=["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Basic SQL injection prevention"""
        # Remove common SQL injection patterns
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
            r'(\b(and|or)\b\s+\d+\s*=\s*\d+)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\')',
            r'(\b(and|or)\b\s+\d+\s*=\s*\'[^\']*\')',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\d+)',
        ]
        
        for pattern in sql_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return filename


class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self, security_provider: ISecurityProvider):
        self.security_provider = security_provider
    
    def process_request(self, request: HttpRequest) -> SecurityContext:
        """Process request and create security context"""
        context = SecurityContext(
            user=getattr(request, 'user', None),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            timestamp=datetime.now()
        )
        
        # Extract token from headers
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            user = self.security_provider.validate_token(token)
            if user:
                context.user = user
        
        # Extract permissions and roles
        if context.user:
            context.permissions = self._get_user_permissions(context.user)
            context.roles = self._get_user_roles(context.user)
        
        return context
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _get_user_permissions(self, user: User) -> List[str]:
        """Get user permissions"""
        permissions = []
        
        # User permissions
        for perm in user.user_permissions.all():
            permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
        
        # Group permissions
        for group in user.groups.all():
            for perm in group.permissions.all():
                permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
        
        return list(set(permissions))
    
    def _get_user_roles(self, user: User) -> List[str]:
        """Get user roles (group names)"""
        return [group.name for group in user.groups.all()]


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            security_provider = SecurityProvider()
            if not security_provider.authorize(request.user, permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not request.user.groups.filter(name=role).exists():
                raise PermissionDenied(f"Role '{role}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_authentication(view_func: Callable) -> Callable:
    """Decorator to require authentication"""
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")
        return view_func(request, *args, **kwargs)
    return wrapper


class SecurityAuditor:
    """Security audit utilities"""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    def log_security_event(self, event_type: str, user: Optional[User], 
                          details: Dict[str, Any], ip_address: Optional[str] = None) -> None:
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'ip_address': ip_address,
            'details': details
        }
        
        self.audit_log.append(event)
        logger.info(f"Security event: {event_type} - User: {user.username if user else 'Anonymous'}")
    
    def get_audit_log(self, event_type: Optional[str] = None, 
                     user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit log with optional filtering"""
        log = self.audit_log.copy()
        
        if event_type:
            log = [event for event in log if event['event_type'] == event_type]
        
        if user_id:
            log = [event for event in log if event['user_id'] == user_id]
        
        return log


# Global instances
security_provider = SecurityProvider()
security_middleware = SecurityMiddleware(security_provider)
security_auditor = SecurityAuditor()


# Convenience functions
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user"""
    credentials = {'username': username, 'password': password}
    return security_provider.authenticate(credentials)


def check_permission(user: User, permission: str) -> bool:
    """Check if user has permission"""
    return security_provider.authorize(user, permission)


def generate_auth_token(user: User, expires_in: int = 3600) -> str:
    """Generate authentication token"""
    return security_provider.generate_token(user, expires_in)


def validate_auth_token(token: str) -> Optional[User]:
    """Validate authentication token"""
    return security_provider.validate_token(token)


def sanitize_input(text: str, input_type: str = "html") -> str:
    """Sanitize input based on type"""
    if input_type == "html":
        return InputSanitizer.sanitize_html(text)
    elif input_type == "sql":
        return InputSanitizer.sanitize_sql(text)
    elif input_type == "filename":
        return InputSanitizer.sanitize_filename(text)
    else:
        return text.strip()


def generate_secure_password(length: int = 12) -> str:
    """Generate secure password"""
    return PasswordSecurity.generate_strong_password(length)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    return PasswordSecurity.validate_password_strength(password) 