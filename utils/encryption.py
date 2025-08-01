import os
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app
import json

class EncryptionManager:
    """Centralized encryption management for MoneyMentor"""
    
    def __init__(self):
        self._encryption_key = None
        self._salt = None
    
    def get_encryption_key(self):
        """Get or generate encryption key"""
        if self._encryption_key:
            return self._encryption_key
        
        # Try to get from environment first
        env_key = current_app.config.get('ENCRYPTION_KEY')
        if env_key:
            self._encryption_key = env_key.encode()
            return self._encryption_key
        
        # Generate new key if not found
        print("⚠️  WARNING: No ENCRYPTION_KEY found. Generating temporary key.")
        print("    This key will be lost when app restarts!")
        print("    Set ENCRYPTION_KEY in your .env file for production.")
        
        self._encryption_key = Fernet.generate_key()
        return self._encryption_key
    
    def generate_salt(self, length=16):
        """Generate cryptographically secure salt"""
        if not self._salt:
            self._salt = secrets.token_bytes(length)
        return self._salt
    
    def derive_key_from_password(self, password, salt=None):
        """Derive encryption key from password using PBKDF2"""
        if not salt:
            salt = self.generate_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

# Global encryption manager instance
encryption_manager = EncryptionManager()

def encrypt_data(data):
    """
    Encrypt sensitive data using Fernet symmetric encryption
    
    Args:
        data (str): Data to encrypt
        
    Returns:
        str: Base64 encoded encrypted data
    """
    if not data:
        return None
    
    try:
        # Get encryption key
        key = encryption_manager.get_encryption_key()
        f = Fernet(key)
        
        # Convert data to bytes if it's not already
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = str(data).encode('utf-8')
        
        # Encrypt and encode
        encrypted_data = f.encrypt(data_bytes)
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        
    except Exception as e:
        current_app.logger.error(f"Encryption failed: {str(e)}")
        raise EncryptionError(f"Failed to encrypt data: {str(e)}")

def decrypt_data(encrypted_data):
    """
    Decrypt data encrypted with encrypt_data function
    
    Args:
        encrypted_data (str): Base64 encoded encrypted data
        
    Returns:
        str: Decrypted data
    """
    if not encrypted_data:
        return None
    
    try:
        # Get encryption key
        key = encryption_manager.get_encryption_key()
        f = Fernet(key)
        
        # Decode and decrypt
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = f.decrypt(encrypted_bytes)
        
        return decrypted_bytes.decode('utf-8')
        
    except Exception as e:
        current_app.logger.error(f"Decryption failed: {str(e)}")
        raise EncryptionError(f"Failed to decrypt data: {str(e)}")

def encrypt_financial_data(financial_dict):
    """
    Encrypt a dictionary of financial data
    
    Args:
        financial_dict (dict): Dictionary containing financial data
        
    Returns:
        str: Encrypted JSON string
    """
    try:
        # Convert dict to JSON string
        json_data = json.dumps(financial_dict, ensure_ascii=False)
        
        # Encrypt the JSON string
        encrypted_json = encrypt_data(json_data)
        
        return encrypted_json
        
    except Exception as e:
        current_app.logger.error(f"Financial data encryption failed: {str(e)}")
        raise EncryptionError(f"Failed to encrypt financial data: {str(e)}")

def decrypt_financial_data(encrypted_json):
    """
    Decrypt financial data back to dictionary
    
    Args:
        encrypted_json (str): Encrypted JSON string
        
    Returns:
        dict: Decrypted financial data dictionary
    """
    try:
        if not encrypted_json:
            return {}
        
        # Decrypt JSON string
        json_data = decrypt_data(encrypted_json)
        
        # Parse JSON back to dictionary
        financial_dict = json.loads(json_data)
        
        return financial_dict
        
    except Exception as e:
        current_app.logger.error(f"Financial data decryption failed: {str(e)}")
        return {}  # Return empty dict instead of raising error

def hash_sensitive_data(data, salt=None):
    """
    Create irreversible hash of sensitive data for logging/analytics
    
    Args:
        data (str): Data to hash
        salt (bytes, optional): Salt for hashing
        
    Returns:
        str: Hexadecimal hash string
    """
    if not data:
        return None
    
    if not salt:
        salt = encryption_manager.generate_salt()
    
    # Use SHA-256 with salt
    hash_obj = hashlib.sha256()
    hash_obj.update(salt)
    hash_obj.update(data.encode('utf-8'))
    
    return hash_obj.hexdigest()

def secure_compare(value1, value2):
    """
    Timing-safe string comparison to prevent timing attacks
    
    Args:
        value1 (str): First value
        value2 (str): Second value
        
    Returns:
        bool: True if values match
    """
    if not value1 or not value2:
        return False
    
    return secrets.compare_digest(str(value1), str(value2))

def generate_secure_token(length=32):
    """
    Generate cryptographically secure random token
    
    Args:
        length (int): Token length in bytes
        
    Returns:
        str: URL-safe base64 encoded token
    """
    token = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(token).decode('utf-8')

def mask_sensitive_data(data, mask_char='*', visible_chars=4):
    """
    Mask sensitive data for display purposes
    
    Args:
        data (str): Data to mask
        mask_char (str): Character to use for masking
        visible_chars (int): Number of characters to keep visible at end
        
    Returns:
        str: Masked data
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    visible_part = data[-visible_chars:] if visible_chars > 0 else ""
    masked_part = mask_char * (len(data) - visible_chars)
    
    return masked_part + visible_part

def encrypt_user_session_data(session_data):
    """
    Encrypt user session data for secure storage
    
    Args:
        session_data (dict): Session data to encrypt
        
    Returns:
        str: Encrypted session data
    """
    try:
        # Remove sensitive fields before encryption
        safe_session_data = {
            'user_id': session_data.get('user_id'),
            'username': hash_sensitive_data(session_data.get('username', '')),
            'login_time': session_data.get('login_time'),
            'preferences': session_data.get('preferences', {})
        }
        
        return encrypt_financial_data(safe_session_data)
        
    except Exception as e:
        current_app.logger.error(f"Session encryption failed: {str(e)}")
        raise EncryptionError(f"Failed to encrypt session data: {str(e)}")

def validate_encryption_key():
    """
    Validate that encryption key is properly configured
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        # Test encryption/decryption
        test_data = "encryption_test_" + generate_secure_token(8)
        encrypted = encrypt_data(test_data)
        decrypted = decrypt_data(encrypted)
        
        if decrypted == test_data:
            return True, "Encryption key is valid"
        else:
            return False, "Encryption key validation failed"
            
    except Exception as e:
        return False, f"Encryption validation error: {str(e)}"

def secure_delete_data(data):
    """
    Securely overwrite data in memory (best effort)
    
    Args:
        data (str): Data to securely delete
    """
    if not data:
        return
    
    try:
        # Overwrite the data multiple times
        for _ in range(3):
            data = 'x' * len(data)
            data = '\x00' * len(data)
        
        del data
        
    except Exception:
        pass  # Best effort cleanup

class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass

class SecureDataHandler:
    """Context manager for handling sensitive data securely"""
    
    def __init__(self, sensitive_data):
        self.data = sensitive_data
        self.processed_data = None
    
    def __enter__(self):
        return self.data
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Securely delete the data
        secure_delete_data(self.data)
        if self.processed_data:
            secure_delete_data(self.processed_data)

# Convenience functions for common encryption patterns

def encrypt_income(income_amount):
    """Encrypt income amount specifically"""
    if not income_amount:
        return None
    return encrypt_data(str(float(income_amount)))

def decrypt_income(encrypted_income):
    """Decrypt income amount specifically"""
    if not encrypted_income:
        return 0.0
    try:
        decrypted = decrypt_data(encrypted_income)
        return float(decrypted)
    except (ValueError, EncryptionError):
        return 0.0

def encrypt_goal_data(goals_list):
    """Encrypt list of financial goals"""
    if not goals_list:
        return None
    return encrypt_financial_data({'goals': goals_list})

def decrypt_goal_data(encrypted_goals):
    """Decrypt list of financial goals"""
    if not encrypted_goals:
        return []
    try:
        decrypted = decrypt_financial_data(encrypted_goals)
        return decrypted.get('goals', [])
    except:
        return []

# Initialize encryption validation on module load
def init_encryption():
    """Initialize and validate encryption on app startup"""
    is_valid, message = validate_encryption_key()
    if not is_valid:
        print(f"⚠️  Encryption Warning: {message}")
    else:
        print("✅ Encryption system initialized successfully")

# Auto-validate when module is imported
try:
    # Only validate if we're in Flask app context
    from flask import has_app_context
    if has_app_context():
        init_encryption()
except ImportError:
    pass  # Flask not available, skip validation
