from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config, Config

# Import models from the models package
from models import db, User, FinancialPlan

import os
import requests
import json
from datetime import datetime, timedelta

# Load environment variables
def load_env_from_file():
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        pass

load_env_from_file()


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

# NEW: API Service for real data
class APIService:
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHAVANTAGE_API_KEY')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MoneyMentor/1.0'})
    
    def fetch_real_mutual_funds_india(self, risk_appetite='moderate'):
        """Fetch real mutual fund data using free MF API"""
        try:
            response = self.session.get("https://api.mfapi.in/mf", timeout=10)
            
            if response.status_code != 200:
                return {'status': 'error', 'data': []}
            
            all_funds = response.json()
            
            # Filter funds based on risk appetite
            risk_keywords = {
                'conservative': ['debt', 'liquid', 'short term', 'gilt'],
                'moderate': ['hybrid', 'balanced', 'large cap', 'bluechip'],
                'aggressive': ['small cap', 'mid cap', 'equity', 'growth']
            }
            
            keywords = risk_keywords.get(risk_appetite, risk_keywords['moderate'])
            filtered_funds = []
            
            for fund in all_funds:
                fund_name_lower = fund['schemeName'].lower()
                if any(keyword in fund_name_lower for keyword in keywords):
                    filtered_funds.append(fund)
            
            # Get top 3 funds with NAV data
            detailed_funds = []
            for fund in filtered_funds[:3]:
                try:
                    nav_response = self.session.get(f"https://api.mfapi.in/mf/{fund['schemeCode']}", timeout=5)
                    if nav_response.status_code == 200:
                        nav_data = nav_response.json()
                        
                        if nav_data.get('data') and len(nav_data['data']) > 0:
                            detailed_funds.append({
                                'name': fund['schemeName'],
                                'scheme_code': fund['schemeCode'],
                                'nav': float(nav_data['data'][0]['nav']),
                                'date': nav_data['data'][0]['date'],
                                'fund_house': fund['schemeName'].split()[0],
                                'category': 'Mutual Fund',
                                'risk_level': f"{risk_appetite.title()} Risk",
                                'min_investment': '₹500 (SIP)'
                            })
                except:
                    continue
            
            return {'status': 'success', 'data': detailed_funds}
            
        except Exception as e:
            return {'status': 'error', 'data': []}
    
    def fetch_real_stock_data(self):
        """Fetch stock data using Alpha Vantage"""
        try:
            if not self.alpha_vantage_key:
                return self._get_fallback_stocks()
            
            stocks = ['TCS.BSE', 'RELIANCE.BSE']
            stock_data = {}
            
            for stock in stocks:
                try:
                    url = "https://www.alphavantage.co/query"
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': stock,
                        'apikey': self.alpha_vantage_key
                    }
                    
                    response = self.session.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'Global Quote' in data and data['Global Quote']:
                            quote = data['Global Quote']
                            stock_name = stock.replace('.BSE', '')
                            
                            stock_data[stock_name] = {
                                'price': float(quote.get('05. price', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': quote.get('10. change percent', '0%')
                            }
                except:
                    continue
            
            # Add fallback data
            fallback = self._get_fallback_stocks()['data']
            for name, data in fallback.items():
                if name not in stock_data:
                    stock_data[name] = data
            
            return {'status': 'success', 'data': stock_data}
            
        except:
            return self._get_fallback_stocks()
    
    def fetch_financial_news(self):
        """Get curated financial news"""
        news_items = [
            {
                'title': 'Indian Markets Show Strong Performance',
                'description': 'Nifty 50 continues upward trend with banking and IT sectors leading gains.',
                'source': 'MoneyMentor News',
                'publishedAt': datetime.now().isoformat(),
                'category': 'market'
            },
            {
                'title': 'SIP Investments Hit Record High',
                'description': 'Monthly SIP contributions cross ₹18,000 crore mark as retail investors show confidence.',
                'source': 'Financial Express',
                'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat(),
                'category': 'mutual_funds'
            }
        ]
        
        return {'status': 'success', 'data': news_items}
    
    def fetch_emergency_fund_options(self):
        """Get emergency fund options"""
        options = [
            {
                'name': 'High-Yield Savings Account',
                'category': 'Bank Account',
                'liquidity': 'Instant access',
                'risk': 'Nil (Government insured)',
                'min_investment': '₹10,000',
                'suitable_for': 'Emergency fund storage - instant access'
            },
            {
                'name': 'Liquid Mutual Fund',
                'category': 'Liquid Fund', 
                'liquidity': 'Same day redemption',
                'risk': 'Very Low',
                'min_investment': '₹1,000',
                'suitable_for': 'Emergency fund - better returns than savings'
            }
        ]
        
        return {'status': 'success', 'data': options}
    
    def _get_fallback_stocks(self):
        """Fallback stock data"""
        return {
            'status': 'success',
            'data': {
                'TCS': {'price': 3856.75, 'change': 42.30, 'change_percent': '+1.11%'},
                'RELIANCE': {'price': 2543.20, 'change': -18.45, 'change_percent': '-0.72%'},
                'HDFCBANK': {'price': 1687.90, 'change': 15.60, 'change_percent': '+0.93%'}
            }
        }

# NEW: Chatbot Service
class ChatbotService:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')
    
    def get_response(self, message, income=0, context=None):
        """Get chatbot response"""
        try:
            if self.openrouter_key:
                return self._get_ai_response(message, income, context)
            else:
                return self._get_rule_based_response(message, income, context)
        except:
            return self._get_rule_based_response(message, income, context)
    
    def _get_ai_response(self, message, income, context):
        """Get AI response from OpenRouter"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            context_info = f"User income: ₹{income:,}/month" if income > 0 else "User hasn't set income yet"
            
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": f"You are MoneyMentor, a helpful Indian financial advisor. {context_info}. Give practical advice in simple language with ₹ amounts. Keep responses under 150 words."
                    },
                    {"role": "user", "content": message}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
            
            return self._get_rule_based_response(message, income, context)
            
        except:
            return self._get_rule_based_response(message, income, context)
    
    def _get_rule_based_response(self, message, income, context):
        """Rule-based responses"""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
            if income > 0:
                return f"🙏 Hello! I can see you earn ₹{income:,} monthly. How can I help you with your finances today?"
            else:
                return "🙏 Hello! I'm your MoneyMentor AI assistant. Please set up your financial plan first!"
        
        if any(word in msg_lower for word in ['budget', 'expenses']):
            if income > 0:
                return f"💡 For ₹{income:,} income: Try 50% needs (₹{income*0.50:,.0f}), 30% wants (₹{income*0.30:,.0f}), 20% savings (₹{income*0.20:,.0f})"
            else:
                return "📋 I'd love to help with budgeting! Please set up your income first."
        
        if any(word in msg_lower for word in ['investment', 'sip', 'mutual fund']):
            if income > 0:
                sip_amount = min(income * 0.15, 20000)
                return f"📈 Great! With ₹{income:,} income, start SIP of ₹{sip_amount:,.0f}/month in balanced mutual funds for long-term growth."
            else:
                return "💰 I can suggest investments! Please set up your financial plan first."
        
        if any(word in msg_lower for word in ['emergency', 'emergency fund']):
            if income > 0:
                emergency = income * 6
                return f"🚨 Emergency fund target: ₹{emergency:,} (6 months expenses). Keep in savings account or liquid funds for instant access!"
            else:
                return "🚨 Emergency fund is crucial! Set up your income first to get specific targets."
        
        # Default response
        if income > 0:
            return f"🤖 I'm here to help with your ₹{income:,} monthly income! Ask me about budgeting, investments, goals, or emergency funds. 💰"
        else:
            return "🤖 I'm your MoneyMentor AI! Set up your financial plan first by entering your income above, then I can give personalized advice! 🚀"

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
            # Try OpenRouter API first
            try:
                openrouter_key = os.getenv('OPENROUTER_API_KEY')
                if openrouter_key:
                    import requests
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": "meta-llama/llama-3.3-70b-instruct:free",
                        "messages": [
                            {"role": "system", "content": f"You are MoneyMentor. User income: ₹{income:,}/month. Give helpful financial advice in 100 words."},
                            {"role": "user", "content": message}
                        ],
                        "max_tokens": 150,
                        "temperature": 0.7
                    }
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
            except:
                pass
            
            # Fallback responses (keep your existing logic)
            msg_lower = message.lower()
            if 'hello' in msg_lower or 'hi' in msg_lower:
                if income > 0:
                    return f"🙏 Hello! I can see you earn ₹{income:,} monthly. How can I help with your finances?"
                else:
                    return "🙏 Hello! Please set up your financial plan first by entering your income above."
            
            if 'budget' in msg_lower:
                if income > 0:
                    return f"💡 For ₹{income:,} income: Try 50% needs (₹{income*0.50:,.0f}), 30% wants (₹{income*0.30:,.0f}), 20% savings (₹{income*0.20:,.0f})"
                return "📋 Please set up your income first for budget advice."
            
            if 'investment' in msg_lower or 'sip' in msg_lower:
                if income > 0:
                    return f"📈 Start SIP of ₹{min(income*0.15, 20000):,.0f}/month in balanced mutual funds for long-term growth."
                return "💰 Set up your income first for investment suggestions."
            
            return "🤖 I can help with budgeting, investments, goals! Ask me anything about your finances."

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
    
    # Initialize agents and services
    budget_agent = BudgetAgent()
    investment_agent = InvestmentAgent()
    goal_agent = GoalAgent()
    tax_agent = TaxAgent()
    llm_agent = LLMAgent()
    
    # NEW: Initialize API services
    api_service = APIService()
    chatbot_service = ChatbotService()
    
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
    
    # NEW: Real API Routes
    @app.route('/api/real-mutual-funds/<risk_appetite>')
    @login_required
    def get_real_mutual_funds(risk_appetite):
        """Fetch real mutual fund data"""
        try:
            import requests
            response = requests.get("https://api.mfapi.in/mf", timeout=10)
            if response.status_code == 200:
                all_funds = response.json()
                # Simple filtering based on risk
                keywords = {
                    'conservative': ['debt', 'liquid'],
                    'moderate': ['balanced', 'large cap'],
                    'aggressive': ['small cap', 'mid cap']
                }
                filter_words = keywords.get(risk_appetite, ['balanced'])
                filtered = [f for f in all_funds if any(w in f['schemeName'].lower() for w in filter_words)]
                return jsonify({'status': 'success', 'data': filtered[:3]})
        except:
            pass
        return jsonify({'status': 'success', 'data': []})


    @app.route('/api/live-financial-news')
    @login_required
    def get_live_financial_news():
        """Fetch financial news"""
        try:
            news_data = api_service.fetch_financial_news()
            return jsonify(news_data)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/api/live-stock-data')
    @login_required
    def get_live_stock_data():
        """Fetch stock data"""
        try:
            stock_data = api_service.fetch_real_stock_data()
            return jsonify(stock_data)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/api/emergency-fund-options')
    @login_required
    def get_emergency_fund_options():
        """Fetch emergency fund options"""
        try:
            emergency_data = api_service.fetch_emergency_fund_options()
            return jsonify(emergency_data)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
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
            
            # Use new chatbot service
            response = chatbot_service.get_response(message, current_user.monthly_income, context)
            
            return jsonify({'response': response})
            
        except Exception as e:
            app.logger.error(f"Chat error: {str(e)}")
            return jsonify({'error': 'Chat service temporarily unavailable'}), 500
    
    # @app.route('/api/real-mutual-funds/<risk_appetite>')
    # @login_required
    # def get_real_mutual_funds(risk_appetite):
    #     """Fetch real mutual fund data"""
    #     try:
    #         response = requests.get("https://api.mfapi.in/mf", timeout=10)
    #         if response.status_code == 200:
    #             all_funds = response.json()
    #             # Simple filtering based on risk
    #             keywords = {
    #                 'conservative': ['debt', 'liquid'],
    #                 'moderate': ['balanced', 'large cap'],
    #                 'aggressive': ['small cap', 'mid cap']
    #             }
    #             filter_words = keywords.get(risk_appetite, ['balanced'])
    #             filtered = [f for f in all_funds if any(w in f['schemeName'].lower() for w in filter_words)]
    #             return jsonify({'status': 'success', 'data': filtered[:3]})
    #     except Exception as e:
    #         app.logger.error(f"Error fetching mutual funds: {str(e)}")
    #         return jsonify({'status': 'success', 'data': []})

    
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
