from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from utils.encryption import encrypt_data, decrypt_data
from utils.privacy import anonymize_for_logs
from . import db  # Import db from models.__init__
import json

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Encrypted financial data
    monthly_income_encrypted = db.Column(db.Text)  # Encrypted income
    risk_appetite = db.Column(db.String(20), default='moderate')
    
    # Privacy and security fields
    email_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    
    # Privacy consent
    privacy_consent = db.Column(db.Boolean, default=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    data_processing_consent = db.Column(db.Boolean, default=False)
    consent_date = db.Column(db.DateTime)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_data_export = db.Column(db.DateTime)
    
    # Relationships
    financial_plans = db.relationship('FinancialPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password with enhanced security"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:100000')
    
    def check_password(self, password):
        """Check password and handle failed attempts"""
        if self.is_account_locked():
            return False
        
        is_valid = check_password_hash(self.password_hash, password)
        
        if not is_valid:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        else:
            self.failed_login_attempts = 0
            self.account_locked_until = None
            self.last_login = datetime.utcnow()
        
        db.session.commit()
        return is_valid
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until
    
    @property
    def monthly_income(self):
        """Decrypt and return monthly income"""
        if not self.monthly_income_encrypted:
            return 0
        try:
            return float(decrypt_data(self.monthly_income_encrypted))
        except:
            return 0
    
    @monthly_income.setter
    def monthly_income(self, value):
        """Encrypt and store monthly income"""
        if value is not None:
            self.monthly_income_encrypted = encrypt_data(str(value))
    
    def export_data(self):
        """Export user data for GDPR compliance"""
        self.last_data_export = datetime.utcnow()
        db.session.commit()
        
        return {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'monthly_income': self.monthly_income,
            'risk_appetite': self.risk_appetite,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'privacy_consents': {
                'privacy_consent': self.privacy_consent,
                'marketing_consent': self.marketing_consent,
                'data_processing_consent': self.data_processing_consent,
                'consent_date': self.consent_date.isoformat() if self.consent_date else None
            }
        }
    
    def anonymize_data(self):
        """Anonymize user data for logs"""
        return {
            'user_id': f"user_{self.id}",
            'username': anonymize_for_logs(self.username),
            'email': anonymize_for_logs(self.email),
            'income_range': self.get_income_range(),
            'risk_appetite': self.risk_appetite
        }
    
    def get_income_range(self):
        """Return income range instead of exact amount for privacy"""
        income = self.monthly_income
        if income == 0:
            return "not_set"
        elif income < 30000:
            return "0-30k"
        elif income < 50000:
            return "30k-50k"
        elif income < 100000:
            return "50k-100k"
        else:
            return "100k+"
    
    def __repr__(self):
        return f'<User {anonymize_for_logs(self.username)}>'
