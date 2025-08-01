class BudgetAgent:
    def __init__(self):
        # Updated budget rules based on income levels and practical spending patterns
        self.budget_templates = {
            'low_income': {  # Up to ₹50,000
                'needs': 0.65,     # Higher needs percentage for basic living
                'wants': 0.20,     # Limited discretionary spending
                'savings': 0.15,   # Start building savings habit
                'emergency_source': 'savings'  # Emergency from savings portion
            },
            'middle_income': {  # ₹50,000 - ₹2,00,000
                'needs': 0.50,     # Standard 50/30/20 rule
                'wants': 0.30,
                'savings': 0.20,
                'emergency_source': 'wants'  # Can reduce wants for emergency
            },
            'upper_middle': {  # ₹2,00,000 - ₹5,00,000
                'needs': 0.40,     # Reduced needs percentage
                'wants': 0.35,     # More lifestyle spending
                'savings': 0.25,   # Higher savings capacity
                'emergency_source': 'wants'
            },
            'high_income': {  # ₹5,00,000+
                'needs': 0.30,     # Much lower needs percentage
                'wants': 0.40,     # Higher lifestyle and luxury spending
                'savings': 0.30,   # Aggressive savings and investments
                'emergency_source': 'wants'
            }
        }
        
        # Risk appetite adjustments
        self.risk_adjustments = {
            'conservative': {
                'emergency_multiplier': 1.2,  # 20% more emergency fund
                'savings_boost': 0.05,        # 5% more to savings from wants
                'investment_preference': 'debt_heavy'
            },
            'moderate': {
                'emergency_multiplier': 1.0,  # Standard emergency fund
                'savings_boost': 0.0,         # No adjustment
                'investment_preference': 'balanced'
            },
            'aggressive': {
                'emergency_multiplier': 0.8,  # 20% less emergency fund
                'savings_boost': -0.03,       # 3% less to savings (more wants)
                'investment_preference': 'equity_heavy'
            }
        }
    
    def calculate_budget(self, monthly_income, risk_appetite='moderate'):
        """Calculate budget based on income level and risk appetite"""
        
        # Determine income category
        income_category = self.get_income_category(monthly_income)
        base_template = self.budget_templates[income_category]
        risk_adjustment = self.risk_adjustments.get(risk_appetite, self.risk_adjustments['moderate'])
        
        # Apply risk-based adjustments
        adjusted_needs = base_template['needs']
        adjusted_wants = base_template['wants'] - risk_adjustment['savings_boost']
        adjusted_savings = base_template['savings'] + risk_adjustment['savings_boost']
        
        # Ensure percentages don't go negative
        adjusted_wants = max(0.10, adjusted_wants)  # Minimum 10% for wants
        adjusted_savings = max(0.10, adjusted_savings)  # Minimum 10% for savings
        
        # Calculate emergency fund
        emergency_months = 6 * risk_adjustment['emergency_multiplier']
        emergency_fund_needed = monthly_income * emergency_months
        
        budget = {
            'monthly_income': monthly_income,
            'income_category': income_category,
            'risk_profile': risk_appetite,
            'needs': {
                'amount': monthly_income * adjusted_needs,
                'percentage': adjusted_needs * 100,
                'categories': self.get_needs_breakdown(monthly_income, adjusted_needs),
                'description': 'Essential expenses like rent, food, utilities, transport'
            },
            'wants': {
                'amount': monthly_income * adjusted_wants,
                'percentage': adjusted_wants * 100,
                'categories': self.get_wants_breakdown(monthly_income, adjusted_wants, income_category),
                'description': 'Lifestyle expenses, entertainment, dining out, shopping'
            },
            'savings': {
                'amount': monthly_income * adjusted_savings,
                'percentage': adjusted_savings * 100,
                'categories': self.get_savings_breakdown(monthly_income, adjusted_savings, risk_appetite),
                'description': 'Investments, emergency fund, retirement savings'
            },
            'emergency_fund': {
                'target_amount': emergency_fund_needed,
                'months_coverage': emergency_months,
                'monthly_allocation': min(monthly_income * 0.05, emergency_fund_needed / 24),  # Build over 2 years max
                'source': base_template['emergency_source'],
                'priority': 'high' if emergency_months > 6 else 'medium'
            },
            'recommendations': self.get_practical_recommendations(monthly_income, income_category, risk_appetite),
            'investment_strategy': risk_adjustment['investment_preference']
        }
        
        return budget
    
    def get_income_category(self, monthly_income):
        """Determine income category"""
        if monthly_income <= 50000:
            return 'low_income'
        elif monthly_income <= 200000:
            return 'middle_income'
        elif monthly_income <= 500000:
            return 'upper_middle'
        else:
            return 'high_income'
    
    def get_needs_breakdown(self, monthly_income, needs_percentage):
        """Get practical needs breakdown based on income level"""
        needs_amount = monthly_income * needs_percentage
        
        if monthly_income <= 50000:
            return [
                {'name': 'Rent/House EMI', 'amount': needs_amount * 0.40, 'percentage': 40},
                {'name': 'Food & Groceries', 'amount': needs_amount * 0.25, 'percentage': 25},
                {'name': 'Transport', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'name': 'Utilities (Electricity, Phone)', 'amount': needs_amount * 0.10, 'percentage': 10},
                {'name': 'Basic Healthcare', 'amount': needs_amount * 0.10, 'percentage': 10}
            ]
        elif monthly_income <= 200000:
            return [
                {'name': 'Rent/House EMI', 'amount': needs_amount * 0.35, 'percentage': 35},
                {'name': 'Food & Groceries', 'amount': needs_amount * 0.20, 'percentage': 20},
                {'name': 'Transport', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'name': 'Utilities & Bills', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'name': 'Insurance & Healthcare', 'amount': needs_amount * 0.15, 'percentage': 15}
            ]
        else:  # High income
            return [
                {'name': 'Housing (Rent/EMI)', 'amount': needs_amount * 0.30, 'percentage': 30},
                {'name': 'Food & Household', 'amount': needs_amount * 0.20, 'percentage': 20},
                {'name': 'Transport & Car', 'amount': needs_amount * 0.20, 'percentage': 20},
                {'name': 'Utilities & Services', 'amount': needs_amount * 0.15, 'percentage': 15},
                {'name': 'Insurance & Health', 'amount': needs_amount * 0.15, 'percentage': 15}
            ]
    
    def get_wants_breakdown(self, monthly_income, wants_percentage, income_category):
        """Get wants breakdown based on income level"""
        wants_amount = monthly_income * wants_percentage
        
        if income_category == 'low_income':
            return [
                {'name': 'Entertainment & Movies', 'amount': wants_amount * 0.30, 'percentage': 30},
                {'name': 'Eating Out', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'name': 'Shopping & Clothing', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'name': 'Personal Care', 'amount': wants_amount * 0.20, 'percentage': 20}
            ]
        elif income_category in ['middle_income', 'upper_middle']:
            return [
                {'name': 'Dining & Restaurants', 'amount': wants_amount * 0.25, 'percentage': 25},
                {'name': 'Entertainment & Hobbies', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'name': 'Travel & Vacation', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'name': 'Shopping & Lifestyle', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'name': 'Gadgets & Electronics', 'amount': wants_amount * 0.15, 'percentage': 15}
            ]
        else:  # High income
            return [
                {'name': 'Travel & Vacation', 'amount': wants_amount * 0.30, 'percentage': 30},
                {'name': 'Fine Dining & Premium Experiences', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'name': 'Luxury Shopping', 'amount': wants_amount * 0.20, 'percentage': 20},
                {'name': 'Premium Services & Memberships', 'amount': wants_amount * 0.15, 'percentage': 15},
                {'name': 'Gadgets & Technology', 'amount': wants_amount * 0.15, 'percentage': 15}
            ]
    
    def get_savings_breakdown(self, monthly_income, savings_percentage, risk_appetite):
        """Get savings breakdown based on risk appetite"""
        savings_amount = monthly_income * savings_percentage
        
        if risk_appetite == 'conservative':
            return [
                {'name': 'Fixed Deposits', 'amount': savings_amount * 0.30, 'percentage': 30, 'type': 'safe'},
                {'name': 'PPF (Public Provident Fund)', 'amount': savings_amount * 0.25, 'percentage': 25, 'type': 'safe'},
                {'name': 'Safe Mutual Funds', 'amount': savings_amount * 0.20, 'percentage': 20, 'type': 'moderate'},
                {'name': 'NSC & Government Bonds', 'amount': savings_amount * 0.15, 'percentage': 15, 'type': 'safe'},
                {'name': 'Emergency Fund', 'amount': savings_amount * 0.10, 'percentage': 10, 'type': 'liquid'}
            ]
        elif risk_appetite == 'moderate':
            return [
                {'name': 'Mutual Funds (Mixed)', 'amount': savings_amount * 0.40, 'percentage': 40, 'type': 'moderate'},
                {'name': 'PPF', 'amount': savings_amount * 0.20, 'percentage': 20, 'type': 'safe'},
                {'name': 'ELSS (Tax Saving)', 'amount': savings_amount * 0.15, 'percentage': 15, 'type': 'moderate'},
                {'name': 'Fixed Deposits', 'amount': savings_amount * 0.15, 'percentage': 15, 'type': 'safe'},
                {'name': 'Emergency Fund', 'amount': savings_amount * 0.10, 'percentage': 10, 'type': 'liquid'}
            ]
        else:  # Aggressive
            return [
                {'name': 'Stock Market & Equity Funds', 'amount': savings_amount * 0.50, 'percentage': 50, 'type': 'high_risk'},
                {'name': 'Growth Mutual Funds', 'amount': savings_amount * 0.25, 'percentage': 25, 'type': 'moderate'},
                {'name': 'ELSS (Tax Saving)', 'amount': savings_amount * 0.15, 'percentage': 15, 'type': 'moderate'},
                {'name': 'Emergency Fund', 'amount': savings_amount * 0.10, 'percentage': 10, 'type': 'liquid'}
            ]
    
    def get_practical_recommendations(self, monthly_income, income_category, risk_appetite):
        """Get practical, easy-to-understand recommendations"""
        recommendations = []
        
        # Income-based recommendations
        if income_category == 'low_income':
            recommendations.extend([
                "🏠 Keep housing cost under 40% of income to avoid financial stress",
                "🚌 Use public transport or shared rides to save money",
                "🍳 Cook at home more often - it's healthier and cheaper",
                "💰 Start with small savings of ₹1000-2000 per month",
                "📱 Use free apps to track your daily expenses",
                "🏥 Get basic health insurance - medical bills can be expensive"
            ])
        elif income_category == 'middle_income':
            recommendations.extend([
                "🏡 Your housing should not exceed ₹" + f"{int(monthly_income * 0.35):,}" + " per month",
                "🚗 If you have a car loan, total transport cost should be under 15%",
                "💳 Start systematic investments (SIP) of ₹5,000-10,000 monthly",
                "🛡️ Get comprehensive health and term life insurance",
                "💰 Build emergency fund of ₹" + f"{int(monthly_income * 6):,}" + " in 2 years",
                "📊 Review and adjust your budget every 3 months"
            ])
        else:  # High income
            recommendations.extend([
                "💼 You can afford premium lifestyle but don't ignore investments",
                "🏠 Consider buying property if you don't own one",
                "📈 Invest aggressively in equity for wealth building",
                "💰 Emergency fund: ₹" + f"{int(monthly_income * 6):,}" + " is sufficient",
                "🏦 Consider multiple income sources and tax-saving investments",
                "👨‍💼 Hire a financial advisor for complex investment strategies"
            ])
        
        # Risk-based recommendations
        if risk_appetite == 'conservative':
            recommendations.extend([
                "🔒 Focus on safe investments like PPF, FD, and Government bonds",
                "📈 Start with debt mutual funds before moving to equity",
                "💰 Keep 8-9 months of expenses as emergency fund"
            ])
        elif risk_appetite == 'aggressive':
            recommendations.extend([
                "📊 Invest heavily in stock market and equity funds for growth",
                "⏰ You can take risks for higher returns over 5-10 years",
                "💰 4-5 months emergency fund is enough for you"
            ])
        
        # Universal recommendations
        recommendations.extend([
            "📱 Use UPI apps for cashless transactions - helps track spending",
            "📊 Review your budget monthly and adjust as needed",
            "🎯 Set specific financial goals like 'buy car in 3 years'",
            "📚 Learn basics of investing - start with simple mutual funds"
        ])
        
        return recommendations
    
    def calculate_emergency_fund_strategy(self, monthly_income, wants_amount, risk_appetite):
        """Calculate how to build emergency fund practically"""
        target_months = 6 if risk_appetite != 'conservative' else 8
        target_amount = monthly_income * target_months
        
        # Emergency fund should come from wants category, not additional burden
        max_monthly_allocation = wants_amount * 0.20  # 20% of wants money
        months_to_build = target_amount / max_monthly_allocation
        
        return {
            'target_amount': target_amount,
            'target_months_coverage': target_months,
            'monthly_allocation': max_monthly_allocation,
            'time_to_build_months': int(months_to_build),
            'source': 'Reduce entertainment and dining out by this amount',
            'strategy': f"Save ₹{int(max_monthly_allocation):,} monthly by cutting discretionary spending"
        }
    
    def validate_budget_logic(self, budget):
        """Validate that the budget makes practical sense"""
        issues = []
        monthly_income = budget['monthly_income']
        
        # Check if housing cost is reasonable
        housing_cost = budget['needs']['categories'][0]['amount']  # First category is housing
        if housing_cost > monthly_income * 0.5:
            issues.append("Housing cost is too high - should not exceed 50% of income")
        
        # Check if total allocations equal 100%
        total_percentage = budget['needs']['percentage'] + budget['wants']['percentage'] + budget['savings']['percentage']
        if abs(total_percentage - 100) > 1:  # Allow 1% variance for rounding
            issues.append(f"Budget percentages don't add up to 100% (currently {total_percentage:.1f}%)")
        
        # Check if emergency fund allocation is reasonable
        emergency_monthly = budget['emergency_fund']['monthly_allocation']
        if emergency_monthly > monthly_income * 0.10:
            issues.append("Emergency fund allocation is too high - reduce to 10% of income max")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'validation_passed': len(issues) == 0
        }
