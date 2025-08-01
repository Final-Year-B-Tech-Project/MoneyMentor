from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after db is defined to avoid circular imports
from .user import User
from .financial_data import FinancialPlan

__all__ = ['db', 'User', 'FinancialPlan']
