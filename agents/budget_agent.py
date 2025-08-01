from datetime import datetime

class BudgetAgent:
    def __init__(self):
        # Improved budget rules based on income levels
        self.budget_templates = {
            'low_income': {  # Up to ₹50,000
                'needs': 0.60,
                'wants': 0.25, 
                'savings': 0.10,
                'emergency_fund_rate': 0.05,  # 5% for emergency fund
                'emergency_months': 4  # 4 months for low income
            },
            'middle_income': {  # ₹50,000 - ₹2,00,000
                'needs': 0.50,
                'wants': 0.30,
                'savings': 0.15,
                'emergency_fund_rate': 0.05,
                'emergency_months': 6  # 6 months standard
            },
            'upper_middle': {  # ₹2,00,000 - ₹5,00,000
                'needs': 0.45,
                'wants': 0.30,
                'savings': 0.20,
                'emergency_fund_rate': 0.05,
                'emergency_months': 6
            },
            'high_income': {  # ₹5,00,000+
                'needs': 0.40,
                'wants': 0.35,
                'savings': 0.20,
                'emergency_fund_rate': 0.05,
                'emergency_months': 6
            }
        }
        
        # Risk appetite adjustments
        self.risk_adjustments = {
            'conservative': {
                'savings_boost': 0.02,  # 2% more to savings
                'wants_reduction': 0.02,
                'emergency_months_boost': 1  # Extra month
            },
            'moderate': {
                'savings_boost': 0.0,
                'wants_reduction': 0.0,
                'emergency_months_boost': 0
            },
            'aggressive': {
                'savings_boost': 0.03,  # 3% more to savings
                'wants_reduction': 0.03,
                'emergency_months_boost': -1  # One month less
            }
        }
    
    def calculate_budget(self, monthly_income, risk_appetite='moderate'):
        """Calculate budget with proper logic for all income levels"""
        
        # Determine income category
        income_category = self.get_income_category(monthly_income)
        base_template = self.budget_templates[income_category]
        risk_adjustment = self.risk_adjustments.get(risk_appetite, self.risk_adjustments['moderate'])
        
        # Apply risk adjustments
        adjusted_needs = base_template['needs']
        adjusted_wants = base_template['wants'] - risk_adjustment['wants_reduction']
        adjusted_savings = base_template['savings'] + risk_adjustment['savings_boost']
        emergency_months = base_template['emergency_months'] + risk_adjustment['emergency_months_boost']
        
        # Ensure percentages are reasonable
        adjusted_wants = max(0.10, adjusted_wants)  # Minimum 10% for wants
        adjusted_savings = max(0.10, adjusted_savings)  # Minimum 10% for savings
        emergency_months = max(3, emergency_months)  # Minimum 3 months
        
        # Calculate amounts
        needs_amount = monthly_income * adjusted_needs
        wants_amount = monthly_income * adjusted_wants  
        savings_amount = monthly_income * adjusted_savings
        emergency_fund_target = monthly_income * emergency_months
        emergency_monthly = monthly_income * base_template['emergency_fund_rate']
        
        budget = {
            'monthly_income': monthly_income,
            'income_category': income_category,
            'risk_profile': risk_appetite,
            
            'needs': {
                'amount': needs_amount,
                'percentage': adjusted_needs * 100,
                'description': 'Essential expenses: rent, food, transport, utilities',
                'categories': self.get_needs_breakdown(needs_amount, income_category)
            },
            
            'wants': {
                'amount': wants_amount,
                'percentage': adjusted_wants * 100,
                'description': 'Lifestyle expenses: entertainment, dining out, shopping',
                'categories': self.get_wants_breakdown(wants_amount, income_category)
            },
            
            'savings': {
                'amount': savings_amount,
                'percentage': adjusted_savings * 100,
                'description': 'Long-term wealth building investments (NOT emergency fund)',
                'categories': self.get_savings_breakdown(savings_amount, risk_appetite)
            },
            
            'emergency_fund': {
                'target_amount': emergency_fund_target,
                'months_coverage': emergency_months,
                'monthly_contribution': emergency_monthly,
                'percentage_of_income': base_template['emergency_fund_rate'] * 100,
                'storage_options': self.get_emergency_storage_options(),
                'separate_from_investments': True,
                'priority': 'HIGHEST - Build this first!',
                'description': f'Safety net for job loss, medical emergencies - keep in bank/liquid funds'
            },
            
            'recommendations': self.get_practical_recommendations(monthly_income, income_category, risk_appetite),
            'monthly_commitment': needs_amount + wants_amount + savings_amount + emergency_monthly
        }
        
        return budget
    
    def get_income_category(self, monthly_income):
        """Categorize income level"""
        if monthly_income <= 50000:
            return 'low_income'
        elif monthly_income <= 200000:
            return 'middle_income'  
        elif monthly_income <= 500000:
            return 'upper_middle'
        else:
            return 'high_income'
    
    def get_needs_breakdown(self, needs_amount, income_category):
        """Realistic needs breakdown"""
        if income_category == 'low_income':
            return [
                {'category': 'Housing (Rent/EMI)', 'amount': needs_amount * 0.40, 'percentage': 40},
                {'category': 'Food & Groceries', 'amount': needs_amount * 0.30, 'percentage': 30},
                {'category': 'Transport', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'category': 'Utilities & Bills', 'amount': needs_amount * 0.10, 'percentage': 10},
                {'category': 'Basic Insurance', 'amount': needs_amount * 0.05, 'percentage': 5}
            ]
        elif income_category in ['middle_income', 'upper_middle']:
            return [
                {'category': 'Housing (Rent/EMI)', 'amount': needs_amount * 0.35, 'percentage': 35},
                {'category': 'Food & Groceries', 'amount': needs_amount * 0.25, 'percentage': 25},
                {'category': 'Transport & Commute', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'category': 'Utilities & Bills', 'amount': needs_amount * 0.12, 'percentage': 12},
                {'category': 'Insurance & Healthcare', 'amount': needs_amount * 0.13, 'percentage': 13}
            ]
        else:  # high_income
            return [
                {'category': 'Housing (Rent/EMI)', 'amount': needs_amount * 0.30, 'percentage': 30},
                {'category': 'Food & Household', 'amount': needs_amount * 0.20, 'percentage': 20},
                {'category': 'Transport & Car', 'amount': needs_amount * 0.20, 'percentage': 20},
                {'category': 'Utilities & Services', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'category': 'Insurance & Healthcare', 'amount': needs_amount * 0.15, 'percentage': 15}
            ]
    
    def get_wants_breakdown(self, wants_amount, income_category):
        """Lifestyle wants breakdown"""
        if income_category == 'low_income':
            return [
                {'category': 'Entertainment & Movies', 'amount': wants_amount * 0.35, 'percentage': 35},
                {'category': 'Eating Out', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'category': 'Shopping & Clothing', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'category': 'Personal Care & Hobbies', 'amount': wants_amount * 0.15, 'percentage': 15}
            ]
        elif income_category in ['middle_income', 'upper_middle']:
            return [
                {'category': 'Dining & Restaurants', 'amount': wants_amount * 0.30, 'percentage': 30},
                {'category': 'Entertainment & Hobbies', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'category': 'Shopping & Lifestyle', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'category': 'Travel & Weekend Trips', 'amount': wants_amount * 0.15, 'percentage': 15},
                {'category': 'Gadgets & Electronics', 'amount': wants_amount * 0.10, 'percentage': 10}
            ]
        else:  # high_income
            return [
                {'category': 'Travel & Vacations', 'amount': wants_amount * 0.35, 'percentage': 35},
                {'category': 'Fine Dining & Entertainment', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'category': 'Luxury Shopping', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'category': 'Premium Services', 'amount': wants_amount * 0.12, 'percentage': 12},
                {'category': 'Gadgets & Technology', 'amount': wants_amount * 0.08, 'percentage': 8}
            ]
    
    def get_savings_breakdown(self, savings_amount, risk_appetite):
        """Investment allocation based on risk"""
        if risk_appetite == 'conservative':
            return [
                {'category': 'PPF (Tax Saving)', 'amount': savings_amount * 0.30, 'percentage': 30, 'risk': 'Safe'},
                {'category': 'Fixed Deposits', 'amount': savings_amount * 0.25, 'percentage': 25, 'risk': 'Safe'},
                {'category': 'Debt Mutual Funds', 'amount': savings_amount * 0.25, 'percentage': 25, 'risk': 'Low'},
                {'category': 'Large Cap Equity Funds', 'amount': savings_amount * 0.20, 'percentage': 20, 'risk': 'Moderate'}
            ]
        elif risk_appetite == 'moderate':
            return [
                {'category': 'Large Cap Equity Funds', 'amount': savings_amount * 0.40, 'percentage': 40, 'risk': 'Moderate'},
                {'category': 'ELSS (Tax Saving)', 'amount': savings_amount * 0.20, 'percentage': 20, 'risk': 'Moderate'},
                {'category': 'Mid Cap Funds', 'amount': savings_amount * 0.20, 'percentage': 20, 'risk': 'High'},
                {'category': 'Debt Funds', 'amount': savings_amount * 0.20, 'percentage': 20, 'risk': 'Low'}
            ]
        else:  # aggressive
            return [
                {'category': 'Mid & Small Cap Funds', 'amount': savings_amount * 0.40, 'percentage': 40, 'risk': 'High'},
                {'category': 'Large Cap Equity Funds', 'amount': savings_amount * 0.30, 'percentage': 30, 'risk': 'Moderate'},
                {'category': 'ELSS (Tax Saving)', 'amount': savings_amount * 0.20, 'percentage': 20, 'risk': 'Moderate'},
                {'category': 'International Funds', 'amount': savings_amount * 0.10, 'percentage': 10, 'risk': 'High'}
            ]
    
    def get_emergency_storage_options(self):
        """Emergency fund storage recommendations"""
        return [
            {
                'option': 'High-Yield Savings Account',
                'percentage': 50,
                'liquidity': 'Instant',
                'returns': '3.5-4.0%',
                'pros': 'Instant access, ATM cards, UPI, safe',
                'cons': 'Lower returns'
            },
            {
                'option': 'Liquid Mutual Funds', 
                'percentage': 30,
                'liquidity': 'Same day (before 1 PM)',
                'returns': '4.0-4.5%',
                'pros': 'Better returns than savings account',
                'cons': 'Same day redemption limit'
            },
            {
                'option': 'Fixed Deposits (Short-term)',
                'percentage': 20,
                'liquidity': '7-30 days',
                'returns': '5.0-6.0%',
                'pros': 'Higher returns, safe',
                'cons': 'Penalty for early withdrawal'
            }
        ]
    
    def get_practical_recommendations(self, monthly_income, income_category, risk_appetite):
        """Realistic, actionable recommendations"""
        recommendations = []
        
        # Income-specific advice
        if income_category == 'low_income':
            recommendations.extend([
                "🏠 Keep housing cost under 40% of income (₹{:,}) to avoid financial stress".format(int(monthly_income * 0.40)),
                "🚌 Use public transport or shared rides to save on commute costs",
                "🍳 Cook at home more - can save ₹3,000-5,000 monthly on food",
                "💰 Build emergency fund of ₹{:,} gradually - start with ₹{:,}/month".format(int(monthly_income * 4), int(monthly_income * 0.05)),
                "📱 Use expense tracking apps to monitor daily spending",
                "🏥 Get basic health insurance - medical bills can drain savings quickly"
            ])
        elif income_category == 'middle_income':
            recommendations.extend([
                "🏡 Housing should not exceed ₹{:,} monthly for financial comfort".format(int(monthly_income * 0.35)),
                "💳 Start SIP of ₹{:,}-{:,} monthly in diversified mutual funds".format(int(monthly_income * 0.10), int(monthly_income * 0.15)),
                "🛡️ Get comprehensive health insurance and term life insurance",
                "💰 Target emergency fund of ₹{:,} in 18-24 months".format(int(monthly_income * 6)),
                "📊 Review and rebalance investments every 6 months",
                "🎯 Set specific financial goals with timelines"
            ])
        else:  # upper_middle and high_income
            recommendations.extend([
                "💼 You have good earning potential - don't let lifestyle inflation eat all increases",
                "🏠 Consider buying property if you don't own one and plan to stay in city",
                "📈 Invest aggressively in equity for wealth building - target ₹{:,}/month SIP".format(int(monthly_income * 0.20)),
                "💰 Emergency fund target: ₹{:,} - keep in easily accessible options".format(int(monthly_income * 6)),
                "🏦 Consider multiple investment avenues and tax-saving instruments",
                "👨‍💼 Consult a fee-only financial advisor for complex planning"
            ])
        
        # Risk-specific advice
        if risk_appetite == 'conservative':
            recommendations.extend([
                "🔒 Focus on PPF, ELSS, and debt funds for steady growth",
                "📈 Start with large-cap equity funds before mid/small-cap",
                "💰 Keep slightly higher emergency fund (extra month)"
            ])
        elif risk_appetite == 'aggressive':
            recommendations.extend([
                "📊 Invest heavily in equity funds for maximum long-term growth",
                "⏰ Stay invested for 5+ years to ride out market volatility",
                "💰 You can manage with 5 months emergency fund due to risk tolerance"
            ])
        
        # Universal recommendations
        recommendations.extend([
            "📱 Set up auto-debit for SIPs - consistency is key to wealth building",
            "📊 Review your budget quarterly and adjust as income grows",
            "🎯 Have specific goals: 'Buy car in 3 years' not just 'save money'",
            "📚 Learn basics of investing - start with mutual funds before direct stocks",
            "🚨 NEVER invest emergency fund in risky assets - it's your safety net!"
        ])
        
        return recommendations
