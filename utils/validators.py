import re
import bleach
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import current_app
import html

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    """Comprehensive input validation for MoneyMentor"""
    
    # Validation patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[+]?[0-9]{10,15}$',
        'pan': r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
        'aadhar': r'^[0-9]{12}$',
        'ifsc': r'^[A-Z]{4}0[A-Z0-9]{6}$',
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    }
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    
    # Financial limits
    FINANCIAL_LIMITS = {
        'min_income': 1000,
        'max_income': 100000000,  # 10 crores
        'min_investment': 100,
        'max_investment': 50000000,  # 5 crores
        'min_goal_amount': 1000,
        'max_goal_amount': 100000000,
        'min_time_horizon': 0.1,  # 1 month
        'max_time_horizon': 50,   # 50 years
    }

    @classmethod
    def validate_email(cls, email):
        """Validate email format"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")
        
        email = email.strip().lower()
        
        if len(email) > 254:
            raise ValidationError("Email is too long")
        
        if not re.match(cls.PATTERNS['email'], email):
            raise ValidationError("Invalid email format")
        
        return email

    @classmethod
    def validate_username(cls, username):
        """Validate username"""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        
        if len(username) > 20:
            raise ValidationError("Username cannot exceed 20 characters")
        
        if not re.match(cls.PATTERNS['username'], username):
            raise ValidationError("Username can only contain letters, numbers, and underscores")
        
        return username

    @classmethod
    def validate_password(cls, password, check_strength=True):
        """Validate password strength"""
        if not password:
            raise ValidationError("Password is required")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        if len(password) > 128:
            raise ValidationError("Password is too long")
        
        if check_strength:
            if not re.match(cls.PATTERNS['password'], password):
                raise ValidationError(
                    "Password must contain at least: 1 uppercase, 1 lowercase, "
                    "1 number, and 1 special character (@$!%*?&)"
                )
        
        return password

    @classmethod
    def validate_financial_amount(cls, amount, field_name="Amount", min_val=None, max_val=None):
        """Validate financial amounts (income, investment, goals)"""
        if amount is None:
            raise ValidationError(f"{field_name} is required")
        
        try:
            # Convert to float
            if isinstance(amount, str):
                # Remove common formatting
                amount = amount.replace(',', '').replace('₹', '').replace('Rs.', '').strip()
                amount = float(amount)
            else:
                amount = float(amount)
            
            # Check for negative values
            if amount < 0:
                raise ValidationError(f"{field_name} cannot be negative")
            
            # Use provided limits or defaults
            min_limit = min_val or cls.FINANCIAL_LIMITS['min_income']
            max_limit = max_val or cls.FINANCIAL_LIMITS['max_income']
            
            if amount < min_limit:
                raise ValidationError(f"{field_name} must be at least ₹{min_limit:,}")
            
            if amount > max_limit:
                raise ValidationError(f"{field_name} cannot exceed ₹{max_limit:,}")
            
            # Round to 2 decimal places
            return round(amount, 2)
            
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError(f"Invalid {field_name.lower()} format")

    @classmethod
    def validate_income(cls, income):
        """Validate monthly income"""
        return cls.validate_financial_amount(
            income, 
            "Monthly Income",
            cls.FINANCIAL_LIMITS['min_income'],
            cls.FINANCIAL_LIMITS['max_income']
        )

    @classmethod
    def validate_investment_amount(cls, amount):
        """Validate investment amount"""
        return cls.validate_financial_amount(
            amount,
            "Investment Amount", 
            cls.FINANCIAL_LIMITS['min_investment'],
            cls.FINANCIAL_LIMITS['max_investment']
        )

    @classmethod
    def validate_goal_amount(cls, amount):
        """Validate goal target amount"""
        return cls.validate_financial_amount(
            amount,
            "Goal Amount",
            cls.FINANCIAL_LIMITS['min_goal_amount'], 
            cls.FINANCIAL_LIMITS['max_goal_amount']
        )

    @classmethod
    def validate_time_horizon(cls, years):
        """Validate time horizon for goals"""
        if years is None:
            raise ValidationError("Time horizon is required")
        
        try:
            years = float(years)
            
            if years < cls.FINANCIAL_LIMITS['min_time_horizon']:
                raise ValidationError(f"Time horizon must be at least {cls.FINANCIAL_LIMITS['min_time_horizon']} years")
            
            if years > cls.FINANCIAL_LIMITS['max_time_horizon']:
                raise ValidationError(f"Time horizon cannot exceed {cls.FINANCIAL_LIMITS['max_time_horizon']} years")
            
            return years
            
        except (ValueError, TypeError):
            raise ValidationError("Invalid time horizon format")

    @classmethod
    def validate_risk_appetite(cls, risk):
        """Validate risk appetite"""
        valid_risks = ['conservative', 'moderate', 'aggressive']
        
        if not risk:
            return 'moderate'  # Default
        
        risk = risk.strip().lower()
        
        if risk not in valid_risks:
            raise ValidationError(f"Risk appetite must be one of: {', '.join(valid_risks)}")
        
        return risk

    @classmethod
    def validate_goal_data(cls, goals_list):
        """Validate list of financial goals"""
        if not isinstance(goals_list, list):
            raise ValidationError("Goals must be a list")
        
        if len(goals_list) > 10:
            raise ValidationError("Cannot have more than 10 goals")
        
        validated_goals = []
        
        for i, goal in enumerate(goals_list):
            if not isinstance(goal, dict):
                raise ValidationError(f"Goal {i+1} must be an object")
            
            # Validate goal name
            name = goal.get('name', '').strip()
            if not name:
                raise ValidationError(f"Goal {i+1} must have a name")
            
            if len(name) > 100:
                raise ValidationError(f"Goal {i+1} name is too long")
            
            # Validate goal amount
            amount = cls.validate_goal_amount(goal.get('amount'))
            
            # Validate time horizon
            time_years = cls.validate_time_horizon(goal.get('time_years'))
            
            # Validate current savings (optional)
            current_savings = 0
            if goal.get('current_savings'):
                current_savings = cls.validate_financial_amount(
                    goal.get('current_savings'),
                    "Current Savings",
                    0,
                    amount  # Cannot exceed goal amount
                )
            
            validated_goals.append({
                'name': sanitize_text(name),
                'amount': amount,
                'time_years': time_years,
                'current_savings': current_savings
            })
        
        return validated_goals

    @classmethod
    def validate_pan_number(cls, pan):
        """Validate PAN number format"""
        if not pan:
            return None  # PAN is optional in many cases
        
        pan = pan.strip().upper()
        
        if not re.match(cls.PATTERNS['pan'], pan):
            raise ValidationError("Invalid PAN format (ABCDE1234F)")
        
        return pan

    @classmethod
    def validate_phone_number(cls, phone):
        """Validate phone number"""
        if not phone:
            return None  # Phone might be optional
        
        # Remove common formatting
        phone = re.sub(r'[^\d+]', '', str(phone))
        
        if not re.match(cls.PATTERNS['phone'], phone):
            raise ValidationError("Invalid phone number format")
        
        return phone

    @classmethod
    def validate_age(cls, age):
        """Validate age"""
        if age is None:
            return None
        
        try:
            age = int(age)
            
            if age < 18:
                raise ValidationError("Age must be at least 18")
            
            if age > 100:
                raise ValidationError("Age cannot exceed 100")
            
            return age
            
        except (ValueError, TypeError):
            raise ValidationError("Invalid age format")

    @classmethod
    def validate_city(cls, city):
        """Validate city name"""
        if not city:
            return None
        
        city = city.strip().title()
        
        if len(city) < 2:
            raise ValidationError("City name is too short")
        
        if len(city) > 50:
            raise ValidationError("City name is too long")
        
        # Only allow letters, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z\s\.-]+$', city):
            raise ValidationError("Invalid city name format")
        
        return city

def sanitize_text(text, max_length=None, allow_html=False):
    """
    Sanitize text input to prevent XSS and other attacks
    
    Args:
        text (str): Input text to sanitize
        max_length (int, optional): Maximum allowed length
        allow_html (bool): Whether to allow safe HTML tags
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text).strip()
    
    # Truncate if too long
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    if allow_html:
        # Allow only safe HTML tags
        text = bleach.clean(
            text, 
            tags=InputValidator.ALLOWED_HTML_TAGS,
            strip=True
        )
    else:
        # Escape HTML entities
        text = html.escape(text)
    
    return text

def sanitize_financial_input(value):
    """
    Sanitize financial input by removing formatting characters
    
    Args:
        value: Input value (string or number)
        
    Returns:
        str: Cleaned financial input
    """
    if not value:
        return "0"
    
    # Convert to string
    value = str(value).strip()
    
    # Remove common currency symbols and formatting
    value = re.sub(r'[₹$,\s]', '', value)
    
    # Keep only digits and decimal points
    value = re.sub(r'[^0-9.]', '', value)
    
    # Handle multiple decimal points
    parts = value.split('.')
    if len(parts) > 2:
        value = parts[0] + '.' + ''.join(parts[1:])
    
    return value or "0"

def validate_input(field_type, value, **kwargs):
    """
    Main validation function - validates input based on field type
    
    Args:
        field_type (str): Type of field to validate
        value: Value to validate  
        **kwargs: Additional validation parameters
        
    Returns:
        Validated and sanitized value
        
    Raises:
        ValidationError: If validation fails
    """
    validator = InputValidator()
    
    validation_methods = {
        'email': validator.validate_email,
        'username': validator.validate_username,
        'password': validator.validate_password,
        'income': validator.validate_income,
        'investment': validator.validate_investment_amount,
        'goal_amount': validator.validate_goal_amount,
        'time_horizon': validator.validate_time_horizon,
        'risk_appetite': validator.validate_risk_appetite,
        'goals': validator.validate_goal_data,
        'pan': validator.validate_pan_number,
        'phone': validator.validate_phone_number,
        'age': validator.validate_age,
        'city': validator.validate_city,
    }
    
    if field_type not in validation_methods:
        raise ValidationError(f"Unknown field type: {field_type}")
    
    try:
        method = validation_methods[field_type]
        if field_type == 'password':
            return method(value, kwargs.get('check_strength', True))
        else:
            return method(value)
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"Validation error for {field_type}: {str(e)}")
        raise ValidationError(f"Validation failed for {field_type}")

def sanitize_input(value, input_type='text', max_length=None):
    """
    Sanitize user input based on input type
    
    Args:
        value: Input value to sanitize
        input_type (str): Type of input ('text', 'financial', 'html')
        max_length (int, optional): Maximum allowed length
        
    Returns:
        Sanitized input value
    """
    if not value:
        return ""
    
    if input_type == 'financial':
        return sanitize_financial_input(value)
    elif input_type == 'html':
        return sanitize_text(value, max_length, allow_html=True)
    else:
        return sanitize_text(value, max_length, allow_html=False)

def validate_api_input(data, required_fields, optional_fields=None):
    """
    Validate API input data structure
    
    Args:
        data (dict): Input data to validate
        required_fields (dict): Required fields with their types
        optional_fields (dict, optional): Optional fields with their types
        
    Returns:
        dict: Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Input data must be a JSON object")
    
    validated_data = {}
    
    # Validate required fields
    for field_name, field_type in required_fields.items():
        if field_name not in data:
            raise ValidationError(f"Required field '{field_name}' is missing")
        
        validated_data[field_name] = validate_input(field_type, data[field_name])
    
    # Validate optional fields
    if optional_fields:
        for field_name, field_type in optional_fields.items():
            if field_name in data and data[field_name] is not None:
                validated_data[field_name] = validate_input(field_type, data[field_name])
    
    return validated_data

# Rate limiting helpers
def is_valid_request_frequency(user_id, endpoint, max_requests_per_minute=60):
    """
    Simple request frequency validation
    Note: In production, use Redis or similar for distributed rate limiting
    
    Args:
        user_id: User identifier
        endpoint: API endpoint
        max_requests_per_minute: Maximum allowed requests
        
    Returns:
        bool: True if request is allowed
    """
    # This is a simplified implementation
    # In production, implement proper rate limiting with Redis
    return True

def validate_file_upload(file, allowed_extensions=None, max_size_mb=5):
    """
    Validate file uploads
    
    Args:
        file: Uploaded file object
        allowed_extensions (list): Allowed file extensions
        max_size_mb (int): Maximum file size in MB
        
    Returns:
        bool: True if file is valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not file:
        raise ValidationError("No file uploaded")
    
    if not file.filename:
        raise ValidationError("No file selected")
    
    # Check file extension
    if allowed_extensions:
        extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if extension not in allowed_extensions:
            raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
    
    # Check file size (simplified - in production, check actual file size)
    # This is just a basic check, implement proper file size validation
    
    return True

# Security validation helpers
def validate_csrf_token(token, session_token):
    """Validate CSRF token"""
    from .encryption import secure_compare
    return secure_compare(token, session_token)

def validate_session_data(session_data):
    """Validate session data integrity"""
    required_fields = ['user_id', 'login_time']
    
    for field in required_fields:
        if field not in session_data:
            return False
    
    # Check session age (24 hours max)
    try:
        login_time = datetime.fromisoformat(session_data['login_time'])
        age = datetime.now() - login_time
        
        if age.total_seconds() > 86400:  # 24 hours
            return False
            
    except (ValueError, TypeError):
        return False
    
    return True
