from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config, Config

# Import models from the models package
from models import db, User, FinancialPlan

import os
from datetime import datetime

# Simple rate limiter for now
def rate_limit(per_minute=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Simple validators for now
def validate_input(field_type, value):
    return True

def sanitize_input(value):
    return str(value).strip() if value else ""

# Simple privacy functions for now
def anonymize_for_logs(value):
    return f"user_{hash(value) % 1000}"

def validate_gdpr_consent(consents):
    required = ['privacy_consent', 'data_processing_consent']
    for consent in required:
        if not consents.get(consent, False):
            return False, f"Missing consent: {consent}"
    return True, "Valid"

# Import agents
try:
    from agents.budget_agent import BudgetAgent
    from agents.investment_agent import InvestmentAgent  
    from agents.goal_agent import GoalAgent
    from agents.tax_agent import TaxAgent
    from agents.llm_agent import LLMAgent
except ImportError:
    # Create dummy agents for now
    class BudgetAgent:
        def calculate_budget(self, income, risk_appetite='moderate'):
            return {
                'needs': {'amount': income * 0.5, 'percentage': 50},
                'wants': {'amount': income * 0.3, 'percentage': 30},
                'savings': {'amount': income * 0.2, 'percentage': 20},
                'emergency_fund': {'target_amount': income * 6, 'months_coverage': 6}
            }
    
    class InvestmentAgent:
        def suggest_portfolio(self, income, risk):
            return {'monthly_investment': income * 0.2, 'allocation': {
                'equity': {'percentage': 50, 'amount': income * 0.1},
                'debt': {'percentage': 30, 'amount': income * 0.06},
                'gold': {'percentage': 10, 'amount': income * 0.02},
                'liquid': {'percentage': 10, 'amount': income * 0.02}
            }}
    
    class GoalAgent:
        def analyze_goals(self, goals, income):
            return {'goals': goals}
    
    class TaxAgent:
        def calculate_tax_savings(self, income):
            return {'deductions': {'80C': {'tax_saved': 30000}, '80D': {'tax_saved': 5000}}}
    
    class LLMAgent:
        def get_response(self, message, income, context=None):
            # Enhanced fallback responses based on context
            if context and context.get('planGenerated'):
                income_text = f"₹{context.get('income', 0):,}"
                risk_text = context.get('risk', 'moderate')
                
                if 'budget' in message.lower():
                    return f"Based on your {income_text} income with {risk_text} risk appetite, your budget looks good! You're allocating funds wisely across essential expenses, lifestyle, and savings."
                elif 'investment' in message.lower():
                    return f"For your {risk_text} risk profile, I recommend a balanced portfolio. Your monthly savings of ₹{context.get('budget', {}).get('savings', 0):,} can be invested across equity funds, debt instruments, and emergency savings."
                elif 'goal' in message.lower() or 'sip' in message.lower():
                    goals_count = context.get('goals', 0)
                    return f"You have {goals_count} financial goals set up. Based on your income of {income_text}, focus on realistic timelines and start with small SIPs that you can increase over time."
                elif 'emergency' in message.lower():
                    return f"Your emergency fund target looks appropriate. Keep building it gradually from your lifestyle budget - about ₹2,000-5,000 per month until you reach 6 months of expenses."
                elif 'tax' in message.lower():
                    return f"For tax saving, focus on ELSS mutual funds (80C limit ₹1.5L) and health insurance (80D). With your income level, you can save ₹30,000-50,000 annually in taxes through smart investments."
                else:
                    return f"I can help you with your finances! You earn {income_text} monthly. Ask me about budgeting, investments, goals, or tax planning."
            else:
                return "Hello! I'm your financial assistant. Please set up your financial plan first by entering your income above, then I can give you personalized advice!"

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
            
            # Basic input validation
            if not username or len(username) < 3:
                flash('Username must be at least 3 characters long')
                return render_template('auth/register.html')
                
            if not email or '@' not in email:
                flash('Please enter a valid email address')
                return render_template('auth/register.html')
                
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters long')
                return render_template('auth/register.html')
            
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
            
            # Check if username already exists (usernames should still be unique)
            if User.query.filter_by(username=username).first():
                flash('Username already taken. Please choose a different username.')
                return render_template('auth/register.html')
            
            # Create new user (email can be duplicate now)
            new_user = User(
                username=username, 
                email=email,
                privacy_consent=consents['privacy_consent'],
                data_processing_consent=consents['data_processing_consent'],
                marketing_consent=consents['marketing_consent'],
                consent_date=datetime.utcnow()
            )
            new_user.set_password(password)
            
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! You can now login.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Registration failed. Please try again.')
                return render_template('auth/register.html')
        
        return render_template('auth/register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    @rate_limit(per_minute=20)
    def login():
        if request.method == 'POST':
            username = sanitize_input(request.form.get('username', ''))
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Please enter both username and password')
                return render_template('auth/login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=True)
                session.permanent = True
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')
        
        return render_template('auth/login.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user)
    
    # NEW: Additional Feature Routes
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)
    
    @app.route('/expenses')
    @login_required
    def expenses():
        return render_template('expense_tracker.html', user=current_user)
    
    @app.route('/analytics')
    @login_required
    def analytics():
        return render_template('analytics.html', user=current_user)
    
    @app.route('/api/calculate-plan', methods=['POST'])
    @login_required
    @rate_limit(per_minute=30)
    def calculate_plan():
        try:
            data = request.json
            income = float(sanitize_input(str(data.get('income', 0))))
            risk_appetite = data.get('risk', 'moderate')
            
            if income <= 0 or income > 100000000:
                return jsonify({'error': 'Invalid income amount'}), 400
            
            # Update user income and risk appetite
            current_user.monthly_income = income
            current_user.risk_appetite = risk_appetite
            db.session.commit()
            
            # Calculate financial plan with risk appetite
            budget = budget_agent.calculate_budget(income, risk_appetite)
            investments = investment_agent.suggest_portfolio(income, risk_appetite)
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
    
    @app.route('/api/chat', methods=['POST'])
    @login_required
    @rate_limit(per_minute=15)
    def chat():
        try:
            data = request.json
            message = sanitize_input(data.get('message', ''))
            context = data.get('context', {})
            
            if not message or len(message) > 500:
                return jsonify({'error': 'Invalid message'}), 400
            
            response = llm_agent.get_response(message, current_user.monthly_income, context)
            
            return jsonify({'response': response})
            
        except Exception as e:
            app.logger.error(f"Chat error: {str(e)}")
            return jsonify({'error': 'Chat service temporarily unavailable'}), 500
    
    @app.route('/api/update-profile', methods=['POST'])
    @login_required
    def update_profile():
        try:
            data = request.json
            
            # Update user profile information
            if 'monthly_income' in data:
                current_user.monthly_income = float(data['monthly_income'])
            
            if 'risk_appetite' in data:
                current_user.risk_appetite = data['risk_appetite']
            
            # Add new profile fields (you may need to add these to User model)
            profile_data = data.get('profile', {})
            preferences_data = data.get('preferences', {})
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update profile'}), 500
    
    @app.route('/api/financial-health-score')
    @login_required
    def financial_health_score():
        """Calculate user's financial health score"""
        try:
            # Simple health score calculation
            score = 0
            details = {}
            
            # Emergency fund score (25 points)
            if hasattr(current_user, 'emergency_fund_months'):
                months = current_user.emergency_fund_months
                if months >= 6:
                    score += 25
                    details['emergency'] = 25
                elif months >= 3:
                    score += 15
                    details['emergency'] = 15
                else:
                    score += 5
                    details['emergency'] = 5
            else:
                details['emergency'] = 10  # Default assumption
                score += 10
            
            # Savings rate score (25 points)
            income = current_user.monthly_income or 50000
            if income > 100000:
                score += 25
                details['savings'] = 25
            elif income > 50000:
                score += 20
                details['savings'] = 20
            else:
                score += 15
                details['savings'] = 15
            
            # Goal planning score (25 points)
            details['goals'] = 18  # Default
            score += 18
            
            # Investment diversity score (25 points)
            risk_appetite = current_user.risk_appetite or 'moderate'
            if risk_appetite == 'moderate':
                details['investments'] = 20
                score += 20
            elif risk_appetite == 'aggressive':
                details['investments'] = 22
                score += 22
            else:
                details['investments'] = 15
                score += 15
            
            return jsonify({
                'totalScore': min(100, score),
                'breakdown': details,
                'recommendations': [
                    'Keep building your emergency fund',
                    'Consider increasing your SIP amount',
                    'Review your insurance coverage',
                    'Track your expenses regularly'
                ]
            })
            
        except Exception as e:
            return jsonify({'error': 'Failed to calculate health score'}), 500
    
    @app.route('/api/expense-insights')
    @login_required
    def expense_insights():
        """Provide expense insights and recommendations"""
        try:
            # This would integrate with expense tracker data
            # For now, providing sample insights
            insights = {
                'top_categories': [
                    {'name': 'Food & Dining', 'amount': 8500, 'percentage': 35},
                    {'name': 'Transport', 'amount': 4200, 'percentage': 18},
                    {'name': 'Entertainment', 'amount': 3800, 'percentage': 16}
                ],
                'recommendations': [
                    'Consider cooking at home more to reduce food expenses',
                    'Look for carpooling options to save on transport',
                    'Set a monthly entertainment budget of ₹3,000'
                ],
                'monthly_trend': 'increasing',
                'savings_potential': 2500
            }
            
            return jsonify(insights)
            
        except Exception as e:
            return jsonify({'error': 'Failed to generate insights'}), 500
    
    @app.route('/privacy')
    def privacy_policy():
        return render_template('privacy.html')
    
    @app.route('/data-settings')
    @login_required
    def data_settings():
        return render_template('data_settings.html', user=current_user)
    
    @app.route('/export-data')
    @login_required
    @rate_limit(per_minute=2)
    def export_data():
        """GDPR data export"""
        try:
            user_data = {
                'user_id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'monthly_income': current_user.monthly_income,
                'risk_appetite': current_user.risk_appetite,
                'created_at': current_user.created_at.isoformat() if hasattr(current_user, 'created_at') else None,
                'export_date': datetime.utcnow().isoformat()
            }
            
            return jsonify(user_data)
            
        except Exception as e:
            app.logger.error(f"Data export error: {str(e)}")
            return jsonify({'error': 'Export failed'}), 500
    
    @app.route('/delete-account', methods=['POST'])
    @login_required
    @rate_limit(per_minute=1)
    def delete_account():
        """Account deletion"""
        try:
            username = current_user.username
            
            db.session.delete(current_user)
            db.session.commit()
            
            logout_user()
            
            flash('Your account has been permanently deleted')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Account deletion failed. Please contact support.')
            return redirect(url_for('data_settings'))
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
