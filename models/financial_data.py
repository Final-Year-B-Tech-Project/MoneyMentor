from datetime import datetime
from utils.encryption import encrypt_data, decrypt_data
from . import db  # Import db from models.__init__
import json

class FinancialPlan(db.Model):
    __tablename__ = 'financial_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Encrypted financial data
    budget_data_encrypted = db.Column(db.Text)
    investment_data_encrypted = db.Column(db.Text)
    goals_data_encrypted = db.Column(db.Text)
    tax_data_encrypted = db.Column(db.Text)
    
    # Metadata
    plan_name = db.Column(db.String(100), default='Default Plan')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_budget_data(self, data):
        """Encrypt and store budget data"""
        self.budget_data_encrypted = encrypt_data(json.dumps(data))
    
    def get_budget_data(self):
        """Decrypt and return budget data"""
        if not self.budget_data_encrypted:
            return {}
        try:
            return json.loads(decrypt_data(self.budget_data_encrypted))
        except:
            return {}
    
    def set_investment_data(self, data):
        """Encrypt and store investment data"""
        self.investment_data_encrypted = encrypt_data(json.dumps(data))
    
    def get_investment_data(self):
        """Decrypt and return investment data"""
        if not self.investment_data_encrypted:
            return {}
        try:
            return json.loads(decrypt_data(self.investment_data_encrypted))
        except:
            return {}
    
    def set_goals_data(self, data):
        """Encrypt and store goals data"""
        self.goals_data_encrypted = encrypt_data(json.dumps(data))
    
    def get_goals_data(self):
        """Decrypt and return goals data"""
        if not self.goals_data_encrypted:
            return {}
        try:
            return json.loads(decrypt_data(self.goals_data_encrypted))
        except:
            return {}
    
    def set_tax_data(self, data):
        """Encrypt and store tax data"""
        self.tax_data_encrypted = encrypt_data(json.dumps(data))
    
    def get_tax_data(self):
        """Decrypt and return tax data"""
        if not self.tax_data_encrypted:
            return {}
        try:
            return json.loads(decrypt_data(self.tax_data_encrypted))
        except:
            return {}
    
    def export_plan(self):
        """Export financial plan for user download"""
        return {
            'plan_id': self.id,
            'plan_name': self.plan_name,
            'budget': self.get_budget_data(),
            'investments': self.get_investment_data(),
            'goals': self.get_goals_data(),
            'tax': self.get_tax_data(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
