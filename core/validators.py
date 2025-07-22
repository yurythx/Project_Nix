"""
Validation System
Provides comprehensive validation utilities for the application
"""
import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator as DjangoEmailValidator, URLValidator as DjangoURLValidator
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data: Optional[Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class IValidator(ABC):
    """Base validator interface"""
    
    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """Validate a value and return result"""
        pass


class BaseValidator(IValidator):
    """Base validator with common functionality"""
    
    def __init__(self, field_name: str = "field"):
        self.field_name = field_name
    
    def validate(self, value: Any) -> ValidationResult:
        """Base validation - always passes"""
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    def add_error(self, result: ValidationResult, message: str) -> None:
        """Add error to validation result"""
        result.errors.append(f"{self.field_name}: {message}")
        result.is_valid = False
    
    def add_warning(self, result: ValidationResult, message: str) -> None:
        """Add warning to validation result"""
        result.warnings.append(f"{self.field_name}: {message}")


class EmailValidator(BaseValidator):
    """Email validation"""
    
    def __init__(self, field_name: str = "email"):
        super().__init__(field_name)
        self.django_validator = DjangoEmailValidator()
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not value:
            self.add_error(result, str(_("Email is required")))
            return result
        
        try:
            self.django_validator(value)
        except ValidationError:
            self.add_error(result, str(_("Invalid email format")))
        
        return result


class URLValidator(BaseValidator):
    """URL validation"""
    
    def __init__(self, field_name: str = "url"):
        super().__init__(field_name)
        self.django_validator = DjangoURLValidator()
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not value:
            return result  # URL is optional
        
        try:
            self.django_validator(value)
        except ValidationError:
            self.add_error(result, str(_("Invalid URL format")))
        
        return result


class PasswordValidator(BaseValidator):
    """Password strength validation"""
    
    def __init__(self, field_name: str = "password", min_length: int = 8):
        super().__init__(field_name)
        self.min_length = min_length
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not value:
            self.add_error(result, str(_("Password is required")))
            return result
        
        if len(value) < self.min_length:
            self.add_error(result, str(_(f"Password must be at least {self.min_length} characters long")))
        
        if not re.search(r'[A-Z]', value):
            self.add_warning(result, str(_("Password should contain at least one uppercase letter")))
        
        if not re.search(r'[a-z]', value):
            self.add_warning(result, str(_("Password should contain at least one lowercase letter")))
        
        if not re.search(r'\d', value):
            self.add_warning(result, str(_("Password should contain at least one digit")))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            self.add_warning(result, str(_("Password should contain at least one special character")))
        
        return result


class PhoneValidator(BaseValidator):
    """Phone number validation"""
    
    def __init__(self, field_name: str = "phone"):
        super().__init__(field_name)
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not value:
            return result  # Phone is optional
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', str(value))
        
        if len(digits_only) < 10:
            self.add_error(result, str(_("Phone number must have at least 10 digits")))
        elif len(digits_only) > 15:
            self.add_error(result, str(_("Phone number cannot have more than 15 digits")))
        
        return result


class LengthValidator(BaseValidator):
    """Length validation"""
    
    def __init__(self, field_name: str = "field", min_length: int = 0, max_length: Optional[int] = None):
        super().__init__(field_name)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if value is None:
            value = ""
        
        value_length = len(str(value))
        
        if value_length < self.min_length:
            self.add_error(result, str(_(f"Must be at least {self.min_length} characters long")))
        
        if self.max_length and value_length > self.max_length:
            self.add_error(result, str(_(f"Cannot exceed {self.max_length} characters")))
        
        return result


class RangeValidator(BaseValidator):
    """Numeric range validation"""
    
    def __init__(self, field_name: str = "field", min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__(field_name)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if value is None:
            return result
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            self.add_error(result, str(_("Must be a valid number")))
            return result
        
        if self.min_value is not None and numeric_value < self.min_value:
            self.add_error(result, str(_(f"Must be at least {self.min_value}")))
        
        if self.max_value is not None and numeric_value > self.max_value:
            self.add_error(result, str(_(f"Cannot exceed {self.max_value}")))
        
        return result


class ChoiceValidator(BaseValidator):
    """Choice validation"""
    
    def __init__(self, field_name: str = "field", choices: List[Any] = None):
        super().__init__(field_name)
        self.choices = choices if choices is not None else []
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if value is None:
            return result
        
        if value not in self.choices:
            self.add_error(result, str(_(f"Must be one of: {', '.join(map(str, self.choices))}")))
        
        return result


class CompositeValidator(BaseValidator):
    """Combines multiple validators"""
    
    def __init__(self, field_name: str = "field", validators: List[IValidator] = None):
        super().__init__(field_name)
        self.validators = validators if validators is not None else []
    
    def validate(self, value: Any) -> ValidationResult:
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        for validator in self.validators:
            validator_result = validator.validate(value)
            result.errors.extend(validator_result.errors)
            result.warnings.extend(validator_result.warnings)
            if not validator_result.is_valid:
                result.is_valid = False
        
        return result


class ValidationManager:
    """Manages validation operations"""
    
    def __init__(self):
        self.validators: Dict[str, IValidator] = {}
    
    def register_validator(self, name: str, validator: IValidator) -> None:
        """Register a validator"""
        self.validators[name] = validator
        logger.info(f"Registered validator: {name}")
    
    def validate_field(self, field_name: str, value: Any, validator_name: str) -> ValidationResult:
        """Validate a field using a registered validator"""
        if validator_name not in self.validators:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown validator: {validator_name}"],
                warnings=[]
            )
        
        validator = self.validators[validator_name]
        return validator.validate(value)
    
    def validate_data(self, data: Dict[str, Any], validation_rules: Dict[str, str]) -> Dict[str, ValidationResult]:
        """Validate multiple fields"""
        results = {}
        
        for field_name, validator_name in validation_rules.items():
            value = data.get(field_name)
            results[field_name] = self.validate_field(field_name, value, validator_name)
        
        return results
    
    def is_data_valid(self, results: Dict[str, ValidationResult]) -> bool:
        """Check if all validation results are valid"""
        return all(result.is_valid for result in results.values())


# Global validation manager instance
validation_manager = ValidationManager()

# Register common validators
validation_manager.register_validator("email", EmailValidator())
validation_manager.register_validator("url", URLValidator())
validation_manager.register_validator("password", PasswordValidator())
validation_manager.register_validator("phone", PhoneValidator())


def validate_email(email: str) -> ValidationResult:
    """Convenience function to validate email"""
    return validation_manager.validate_field("email", email, "email")


def validate_password(password: str) -> ValidationResult:
    """Convenience function to validate password"""
    return validation_manager.validate_field("password", password, "password")


def validate_url(url: str) -> ValidationResult:
    """Convenience function to validate URL"""
    return validation_manager.validate_field("url", url, "url")


def validate_phone(phone: str) -> ValidationResult:
    """Convenience function to validate phone"""
    return validation_manager.validate_field("phone", phone, "phone") 