from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config, Config

# Import models from the models package
from models import db, User, FinancialPlan

# Import utilities (create these files if missing)
# from utils.rate_limiter import rate_limit
# from utils.validators import validate_input, sanitize_input
# from utils.privacy import anonymize_for_logs, validate_gdpr_consent

import os
from datetime import datetime

# Simple rate limiter for now (create utils/rate_limiter.py later)
def rate_limit(per_minute=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Simple validators for now (create utils/validators.py later)
def validate_input(field_type, value):
    return True  # Add proper validation later

def sanitize_input(value):
    return str(value).strip() if value else ""

# Simple privacy functions for now (create utils/privacy.py later)
def anonymize_for_logs(value):
    return f"user_{hash(value) % 1000}"

def validate_gdpr_consent(consents):
    required = ['privacy_consent', 'data_processing_consent']
    for consent in required:
        if not consents.get(consent, False):
            return False, f"Missing consent: {consent}"
    return True, "Valid"

# Import agents (create basic versions if missing)
try:
    from agents.budget_agent import BudgetAgent
    from agents.investment_agent import InvestmentAgent  
    from agents.goal_agent import GoalAgent
    from agents.tax_agent import TaxAgent
    from agents.llm_agent import LLMAgent
except ImportError:
    # Create dummy agents for now
    class BudgetAgent:
        def calculate_budget(self, income):
            return {
                'needs': {'amount': income * 0.5, 'percentage': 50},
                'wants': {'amount': income * 0.3, 'percentage': 30},
                'savings': {'amount': income * 0.2, 'percentage': 20}
            }
    
    class InvestmentAgent:
        def suggest_portfolio(self, income, risk):
            return {'monthly_investment': income * 0.2, 'allocation': {}}
    
    class GoalAgent:
        def analyze_goals(self, goals, income):
            return {'goals': goals}
    
    class TaxAgent:
        def calculate_tax_savings(self, income):
            return {'deductions': {'80C': {'tax_saved': 30000}, '80D': {'tax_saved': 5000}}}
    
    class LLMAgent:
        def get_response(self, message, income):
            return "AI response temporarily unavailable. Please try again later."

def create_app(config_name=None):
    """Application factory with privacy enhancements"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize agents
    budget_agent = BudgetAgent()
    investment_agent = InvestmentAgent()
    goal_agent = GoalAgent()
    tax_agent = TaxAgent()
    llm_agent = LLMAgent()
    
    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('auth/login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    @rate_limit(per_minute=10)
    def register():
        if request.method == 'POST':
            username = sanitize_input(request.form.get('username', ''))
            email = sanitize_input(request.form.get('email', ''))
            password = request.form.get('password', '')
            
            # Basic consent handling
            consents = {
                'privacy_consent': request.form.get('privacy_consent') == 'on',
                'data_processing_consent': request.form.get('data_processing_consent') == 'on',
                'marketing_consent': request.form.get('marketing_consent') == 'on'
            }
            
            is_valid, message = validate_gdpr_consent(consents)
            if not is_valid:
                flash(f'Privacy consent required: {message}')
                return render_template('auth/register.html')
            
            # Check if user exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('auth/register.html')
            
            # Create new user
            new_user = User(
                username=username, 
                email=email,
                privacy_consent=consents['privacy_consent'],
                data_processing_consent=consents['data_processing_consent'],
                marketing_consent=consents['marketing_consent'],
                consent_date=datetime.utcnow()
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    @rate_limit(per_minute=20)
    def login():
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email', ''))
            password = request.form.get('password', '')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user, remember=True)
                session.permanent = True
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials')
        
        return render_template('auth/login.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user)
    
    @app.route('/api/calculate-plan', methods=['POST'])
    @login_required
    @rate_limit(per_minute=30)
    def calculate_plan():
        try:
            data = request.json
            income = float(sanitize_input(str(data.get('income', 0))))
            
            if income <= 0 or income > 10000000:
                return jsonify({'error': 'Invalid income amount'}), 400
            
            # Update user income securely
            current_user.monthly_income = income
            db.session.commit()
            
            # Calculate financial plan
            budget = budget_agent.calculate_budget(income)
            investments = investment_agent.suggest_portfolio(income, current_user.risk_appetite)
            goal_analysis = goal_agent.analyze_goals(data.get('goals', []), income)
            tax_savings = tax_agent.calculate_tax_savings(income * 12)
            
            return jsonify({
                'budget': budget,
                'investments': investments,
                'goals': goal_analysis,
                'tax': tax_savings
            })
            
        except Exception as e:
            app.logger.error(f"Error calculating plan: {str(e)}")
            return jsonify({'error': 'Calculation failed'}), 500
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
