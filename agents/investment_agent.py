import math

class InvestmentAgent:
    def __init__(self):
        # Indian investment options with expected returns and risk levels
        self.investment_options = {
            'equity': {
                'instruments': [
                    {'name': 'Large Cap Funds', 'return': 12, 'risk': 15, 'liquidity': 'high'},
                    {'name': 'Mid Cap Funds', 'return': 15, 'risk': 25, 'liquidity': 'medium'},
                    {'name': 'Small Cap Funds', 'return': 18, 'risk': 35, 'liquidity': 'medium'},
                    {'name': 'ELSS Funds', 'return': 14, 'risk': 20, 'liquidity': 'low'},
                    {'name': 'Index Funds', 'return': 11, 'risk': 12, 'liquidity': 'high'}
                ]
            },
            'debt': {
                'instruments': [
                    {'name': 'PPF', 'return': 7.1, 'risk': 0, 'liquidity': 'very_low'},
                    {'name': 'NSC', 'return': 6.8, 'risk': 0, 'liquidity': 'low'},
                    {'name': 'Corporate Bonds', 'return': 8, 'risk': 5, 'liquidity': 'medium'},
                    {'name': 'Debt Funds', 'return': 7, 'risk': 3, 'liquidity': 'high'},
                    {'name': 'FD', 'return': 5.5, 'risk': 0, 'liquidity': 'medium'}
                ]
            },
            'alternative': {
                'instruments': [
                    {'name': 'Gold ETF', 'return': 8, 'risk': 15, 'liquidity': 'high'},
                    {'name': 'REITs', 'return': 10, 'risk': 18, 'liquidity': 'medium'},
                    {'name': 'Commodity Funds', 'return': 9, 'risk': 20, 'liquidity': 'medium'}
                ]
            },
            'liquid': {
                'instruments': [
                    {'name': 'Liquid Funds', 'return': 4, 'risk': 1, 'liquidity': 'very_high'},
                    {'name': 'Ultra Short Duration Funds', 'return': 5, 'risk': 2, 'liquidity': 'high'},
                    {'name': 'Savings Account', 'return': 3, 'risk': 0, 'liquidity': 'very_high'}
                ]
            }
        }
        
        # Risk-based portfolio allocation templates
        self.portfolio_templates = {
            'conservative': {
                'equity': 20, 'debt': 60, 'alternative': 10, 'liquid': 10,
                'description': 'Low risk, stable returns, capital protection focused'
            },
            'moderate': {
                'equity': 50, 'debt': 30, 'alternative': 10, 'liquid': 10,
                'description': 'Balanced risk-return, good for long-term wealth building'
            },
            'aggressive': {
                'equity': 70, 'debt': 15, 'alternative': 10, 'liquid': 5,
                'description': 'High risk, high return potential, long-term growth focused'
            }
        }
    
    def suggest_portfolio(self, monthly_income, risk_appetite, investment_amount=None, time_horizon=10):
        """Suggest investment portfolio based on Modern Portfolio Theory principles"""
        
        # Calculate investment amount (20% of income if not specified)
        if not investment_amount:
            investment_amount = monthly_income * 0.20
        
        # Get base allocation
        base_allocation = self.portfolio_templates.get(risk_appetite, self.portfolio_templates['moderate'])
        
        # Adjust allocation based on income and time horizon
        adjusted_allocation = self.adjust_allocation_by_income(base_allocation, monthly_income, time_horizon)
        
        # Calculate specific investments
        portfolio = {
            'monthly_investment': investment_amount,
            'annual_investment': investment_amount * 12,
            'risk_profile': risk_appetite,
            'time_horizon': time_horizon,
            'expected_annual_return': 0,
            'risk_score': 0,
            'allocation': {},
            'recommended_funds': {},
            'sip_suggestions': [],
            'tax_benefits': {}
        }
        
        total_expected_return = 0
        total_risk_score = 0
        
        # Calculate allocation for each category
        for category, percentage in adjusted_allocation.items():
            if category == 'description':
                continue
                
            category_amount = investment_amount * (percentage / 100)
            
            # Get best instruments for this category
            best_instruments = self.select_best_instruments(category, risk_appetite)
            
            portfolio['allocation'][category] = {
                'amount': category_amount,
                'percentage': percentage,
                'instruments': best_instruments,
                'monthly_sip': category_amount
            }
            
            # Calculate weighted returns and risk
            for instrument in best_instruments:
                weight = instrument['weight'] / 100
                total_expected_return += (percentage / 100) * weight * instrument['return']
                total_risk_score += (percentage / 100) * weight * instrument['risk']
        
        portfolio['expected_annual_return'] = round(total_expected_return, 2)
        portfolio['risk_score'] = round(total_risk_score, 2)
        
        # Generate specific fund recommendations
        portfolio['recommended_funds'] = self.get_specific_fund_recommendations(adjusted_allocation, investment_amount)
        
        # Generate SIP suggestions
        portfolio['sip_suggestions'] = self.generate_sip_suggestions(investment_amount, adjusted_allocation)
        
        # Calculate tax benefits
        portfolio['tax_benefits'] = self.calculate_tax_benefits(portfolio['allocation'])
        
        # Add rebalancing strategy
        portfolio['rebalancing_strategy'] = self.get_rebalancing_strategy(risk_appetite)
        
        return portfolio
    
    def adjust_allocation_by_income(self, base_allocation, income, time_horizon):
        """Adjust portfolio allocation based on income level and time horizon"""
        adjusted = base_allocation.copy()
        
        # Income-based adjustments
        if income < 30000:  # Lower income
            # More conservative, focus on liquid and debt
            adjusted['equity'] = max(adjusted['equity'] - 10, 10)
            adjusted['debt'] = min(adjusted['debt'] + 5, 70)
            adjusted['liquid'] = min(adjusted['liquid'] + 5, 20)
            
        elif income > 150000:  # Higher income
            # Can take more risk, reduce liquid allocation
            adjusted['equity'] = min(adjusted['equity'] + 10, 80)
            adjusted['liquid'] = max(adjusted['liquid'] - 5, 5)
            adjusted['alternative'] = min(adjusted['alternative'] + 5, 15)
        
        # Time horizon adjustments
        if time_horizon < 3:  # Short term
            adjusted['equity'] = max(adjusted['equity'] - 20, 10)
            adjusted['debt'] = min(adjusted['debt'] + 10, 60)
            adjusted['liquid'] = min(adjusted['liquid'] + 10, 30)
            
        elif time_horizon > 15:  # Very long term
            adjusted['equity'] = min(adjusted['equity'] + 15, 85)
            adjusted['debt'] = max(adjusted['debt'] - 10, 10)
        
        # Ensure total is 100%
        total = sum(v for k, v in adjusted.items() if k != 'description')
        for key in ['equity', 'debt', 'alternative', 'liquid']:
            adjusted[key] = round(adjusted[key] * 100 / total)
        
        return adjusted
    
    def select_best_instruments(self, category, risk_appetite):
        """Select best instruments for each category based on risk appetite"""
        instruments = self.investment_options[category]['instruments']
        
        if risk_appetite == 'conservative':
            # Prefer lower risk instruments
            selected = sorted(instruments, key=lambda x: x['risk'])[:3]
            weights = [50, 30, 20]  # Concentrate on safest
            
        elif risk_appetite == 'aggressive':
            # Prefer higher return instruments
            selected = sorted(instruments, key=lambda x: x['return'], reverse=True)[:3]
            weights = [50, 30, 20]  # Concentrate on highest return
            
        else:  # moderate
            # Balanced approach
            selected = instruments[:3] if len(instruments) >= 3 else instruments
            weights = [40, 35, 25] if len(selected) == 3 else [60, 40] if len(selected) == 2 else [100]
        
        # Add weights to selected instruments
        for i, instrument in enumerate(selected):
            instrument['weight'] = weights[i] if i < len(weights) else 0
        
        return selected
    
    def get_specific_fund_recommendations(self, allocation, investment_amount):
        """Get specific mutual fund recommendations"""
        recommendations = {}
        
        # Equity Fund Recommendations
        if allocation['equity'] > 0:
            equity_amount = investment_amount * (allocation['equity'] / 100)
            recommendations['equity'] = {
                'amount': equity_amount,
                'funds': [
                    {'name': 'SBI Blue Chip Fund', 'category': 'Large Cap', 'expense_ratio': 0.69, 'rating': 4},
                    {'name': 'Mirae Asset Large Cap Fund', 'category': 'Large Cap', 'expense_ratio': 0.52, 'rating': 5},
                    {'name': 'Axis Bluechip Fund', 'category': 'Large Cap', 'expense_ratio': 0.46, 'rating': 4}
                ]
            }
        
        # Debt Fund Recommendations  
        if allocation['debt'] > 0:
            debt_amount = investment_amount * (allocation['debt'] / 100)
            recommendations['debt'] = {
                'amount': debt_amount,
                'funds': [
                    {'name': 'PPF Account', 'category': 'Government', 'return': 7.1, 'tax_benefit': '80C'},
                    {'name': 'HDFC Corporate Bond Fund', 'category': 'Corporate Bond', 'expense_ratio': 0.45, 'rating': 4},
                    {'name': 'ICICI Prudential Corporate Bond Fund', 'category': 'Corporate Bond', 'expense_ratio': 0.42, 'rating': 4}
                ]
            }
        
        return recommendations
    
    def generate_sip_suggestions(self, total_amount, allocation):
        """Generate SIP suggestions with specific amounts"""
        suggestions = []
        
        for category, percentage in allocation.items():
            if category == 'description' or percentage == 0:
                continue
                
            category_amount = total_amount * (percentage / 100)
            
            if category == 'equity' and category_amount >= 1000:
                suggestions.append({
                    'type': 'Equity SIP',
                    'amount': int(category_amount),
                    'frequency': 'Monthly',
                    'suggested_funds': ['Large Cap Fund', 'ELSS Fund'],
                    'min_duration': '5 years',
                    'tax_benefits': 'ELSS qualifies for 80C'
                })
            
            elif category == 'debt' and category_amount >= 500:
                suggestions.append({
                    'type': 'Debt Investment',
                    'amount': int(category_amount),
                    'frequency': 'Monthly',
                    'suggested_funds': ['PPF', 'Corporate Bond Fund'],
                    'min_duration': '3 years',
                    'tax_benefits': 'PPF qualifies for 80C'
                })
        
        return suggestions
    
    def calculate_tax_benefits(self, allocation):
        """Calculate potential tax benefits from investments"""
        benefits = {}
        
        # ELSS benefits (part of equity allocation)
        if 'equity' in allocation:
            elss_amount = min(allocation['equity']['amount'] * 0.3, 150000/12)  # 30% of equity, max 1.5L annually
            benefits['80C_ELSS'] = {
                'monthly_investment': elss_amount,
                'annual_investment': elss_amount * 12,
                'tax_saved_annually': elss_amount * 12 * 0.20,  # Assuming 20% tax bracket
                'lock_in_period': '3 years'
            }
        
        # PPF benefits (part of debt allocation)  
        if 'debt' in allocation:
            ppf_amount = min(allocation['debt']['amount'] * 0.5, 150000/12)  # 50% of debt, max 1.5L annually
            benefits['80C_PPF'] = {
                'monthly_investment': ppf_amount,
                'annual_investment': ppf_amount * 12,
                'tax_saved_annually': ppf_amount * 12 * 0.20,
                'lock_in_period': '15 years'
            }
        
        return benefits
    
    def get_rebalancing_strategy(self, risk_appetite):
        """Suggest portfolio rebalancing strategy"""
        strategies = {
            'conservative': {
                'frequency': 'Annually',
                'trigger': 'If any asset class deviates >10% from target',
                'method': 'Systematic rebalancing on fixed dates'
            },
            'moderate': {
                'frequency': 'Semi-annually', 
                'trigger': 'If any asset class deviates >15% from target',
                'method': 'Threshold-based rebalancing'
            },
            'aggressive': {
                'frequency': 'Quarterly',
                'trigger': 'If equity allocation deviates >20% from target',
                'method': 'Dynamic rebalancing based on market conditions'
            }
        }
        
        return strategies.get(risk_appetite, strategies['moderate'])
    
    def calculate_future_value(self, monthly_sip, annual_return, years):
        """Calculate future value of SIP investments"""
        monthly_return = annual_return / 12 / 100
        months = years * 12
        
        if monthly_return == 0:
            return monthly_sip * months
        
        future_value = monthly_sip * (((1 + monthly_return) ** months - 1) / monthly_return) * (1 + monthly_return)
        return round(future_value, 2)
    
    def get_investment_projections(self, portfolio, years_list=[5, 10, 15, 20]):
        """Get investment projections for different time horizons"""
        projections = {}
        
        monthly_sip = portfolio['monthly_investment']
        expected_return = portfolio['expected_annual_return']
        
        for years in years_list:
            future_value = self.calculate_future_value(monthly_sip, expected_return, years)
            total_invested = monthly_sip * 12 * years
            gains = future_value - total_invested
            
            projections[f'{years}_years'] = {
                'future_value': future_value,
                'total_invested': total_invested,
                'gains': gains,
                'returns_multiple': round(future_value / total_invested, 2)
            }
        
        return projections
