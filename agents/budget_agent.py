class BudgetAgent:
    def __init__(self):
        self.rules = {
            'low_income': {'threshold': 30000, 'needs': 0.60, 'wants': 0.25, 'savings': 0.15},
            'middle_income': {'threshold': 100000, 'needs': 0.50, 'wants': 0.30, 'savings': 0.20},
            'high_income': {'threshold': float('inf'), 'needs': 0.45, 'wants': 0.25, 'savings': 0.30}
        }
    
    def calculate_budget(self, monthly_income):
        """Calculate budget based on 50/30/20 rule with Indian adjustments"""
        
        # Determine income category
        if monthly_income <= 30000:
            category = 'low_income'
        elif monthly_income <= 100000:
            category = 'middle_income'
        else:
            category = 'high_income'
        
        rule = self.rules[category]
        needs_pct = rule['needs']
        wants_pct = rule['wants']
        savings_pct = rule['savings']
        
        budget = {
            'monthly_income': monthly_income,
            'income_category': category,
            'needs': {
                'amount': monthly_income * needs_pct,
                'percentage': needs_pct * 100,
                'categories': [
                    {'name': 'Rent/EMI', 'suggested_pct': 30, 'amount': monthly_income * needs_pct * 0.30},
                    {'name': 'Groceries', 'suggested_pct': 15, 'amount': monthly_income * needs_pct * 0.15},
                    {'name': 'Utilities', 'suggested_pct': 10, 'amount': monthly_income * needs_pct * 0.10},
                    {'name': 'Transport', 'suggested_pct': 10, 'amount': monthly_income * needs_pct * 0.10},
                    {'name': 'Insurance & Healthcare', 'suggested_pct': 15, 'amount': monthly_income * needs_pct * 0.15},
                    {'name': 'Other Essentials', 'suggested_pct': 20, 'amount': monthly_income * needs_pct * 0.20}
                ]
            },
            'wants': {
                'amount': monthly_income * wants_pct,
                'percentage': wants_pct * 100,
                'categories': [
                    {'name': 'Entertainment', 'suggested_pct': 25, 'amount': monthly_income * wants_pct * 0.25},
                    {'name': 'Dining Out', 'suggested_pct': 20, 'amount': monthly_income * wants_pct * 0.20},
                    {'name': 'Shopping', 'suggested_pct': 25, 'amount': monthly_income * wants_pct * 0.25},
                    {'name': 'Travel & Vacation', 'suggested_pct': 20, 'amount': monthly_income * wants_pct * 0.20},
                    {'name': 'Hobbies', 'suggested_pct': 10, 'amount': monthly_income * wants_pct * 0.10}
                ]
            },
            'savings': {
                'amount': monthly_income * savings_pct,
                'percentage': savings_pct * 100,
                'categories': [
                    {'name': 'Emergency Fund', 'suggested_pct': 25, 'amount': monthly_income * savings_pct * 0.25},
                    {'name': 'SIP/Mutual Funds', 'suggested_pct': 40, 'amount': monthly_income * savings_pct * 0.40},
                    {'name': 'PPF', 'suggested_pct': 15, 'amount': monthly_income * savings_pct * 0.15},
                    {'name': 'ELSS (Tax Saving)', 'suggested_pct': 10, 'amount': monthly_income * savings_pct * 0.10},
                    {'name': 'Gold/Other Assets', 'suggested_pct': 10, 'amount': monthly_income * savings_pct * 0.10}
                ]
            },
            'recommendations': self.get_recommendations(monthly_income, category)
        }
        
        return budget
    
    def get_recommendations(self, income, category):
        """Get personalized budget recommendations"""
        recommendations = []
        
        if category == 'low_income':
            recommendations.extend([
                "Focus on building emergency fund first (₹50,000-₹1,00,000)",
                "Consider low-cost mutual funds like index funds",
                "Maximize employer PF contribution if available",
                "Use public transport to reduce expenses"
            ])
        elif category == 'middle_income':
            recommendations.extend([
                "Aim for 6-month emergency fund (₹3-6 lakhs)",
                "Start SIP in diversified equity funds",
                "Utilize Section 80C for tax savings",
                "Consider term insurance (10-15x annual income)"
            ])
        else:  # high_income
            recommendations.extend([
                "Build 12-month emergency fund",
                "Diversify across equity, debt, and alternative investments",
                "Consider ELSS funds for tax optimization",
                "Explore NPS for additional tax benefits",
                "Consider real estate or gold investments"
            ])
        
        return recommendations
    
    def adjust_budget(self, current_budget, adjustments):
        """Allow users to adjust budget percentages"""
        total_adjustment = sum(adjustments.values())
        
        if total_adjustment != 100:
            raise ValueError("Total adjustments must equal 100%")
        
        adjusted_budget = current_budget.copy()
        income = current_budget['monthly_income']
        
        for category, percentage in adjustments.items():
            if category in ['needs', 'wants', 'savings']:
                adjusted_budget[category]['amount'] = income * (percentage / 100)
                adjusted_budget[category]['percentage'] = percentage
        
        return adjusted_budget
