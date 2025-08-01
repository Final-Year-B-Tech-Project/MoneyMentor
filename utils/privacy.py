import hashlib
import re
from flask import current_app

def anonymize_for_logs(text):
    """Anonymize sensitive data for logging"""
    if not text or not current_app.config.get('ANONYMIZE_LOGS', True):
        return text
    
    # Hash the text for consistent anonymization
    hashed = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"anon_{hashed}"

def anonymize_email(email):
    """Anonymize email for privacy"""
    if '@' not in email:
        return anonymize_for_logs(email)
    
    username, domain = email.split('@', 1)
    if len(username) <= 2:
        masked_username = '*' * len(username)
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"

def validate_gdpr_consent(user_consents):
    """Validate GDPR consent requirements"""
    required_consents = ['privacy_consent', 'data_processing_consent']
    
    for consent in required_consents:
        if not user_consents.get(consent, False):
            return False, f"Missing required consent: {consent}"
    
    return True, "All consents valid"

def clean_financial_data_for_export(data):
    """Clean financial data for export (remove internal IDs, etc.)"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key.endswith('_id') or key.startswith('internal_'):
                continue
            cleaned[key] = clean_financial_data_for_export(value)
        return cleaned
    elif isinstance(data, list):
        return [clean_financial_data_for_export(item) for item in data]
    else:
        return data
