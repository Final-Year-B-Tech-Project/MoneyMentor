class TaxAgent:
    def __init__(self):
        # Current Indian tax slabs (2024-25) - New vs Old regime
        self.tax_slabs = {
            'new_regime': [
                (300000, 0),      # Up to 3L - 0%
                (600000, 0.05),   # 3L to 6L - 5%
                (900000, 0.10),   # 6L to 9L - 10%
                (1200000, 0.15),  # 9L to 12L - 15%
                (1500000, 0.20),  # 12L to 15L - 20%
                (float('inf'), 0.30)  # Above 15L - 30%
            ],
            'old_regime': [
                (250000, 0),      # Up to 2.5L - 0%
                (500000, 0.05),   # 2.5L to 5L - 5%
                (1000000, 0.20),  # 5L to 10L - 20%
                (float('inf'), 0.30)  # Above 10L - 30%
            ]
        }
        
        # Tax deduction sections and limits
        self.deduction_sections = {
            '80C': {
                'limit': 150000,
                'options': [
                    {'name': 'ELSS Mutual Funds', 'lock_in': '3 years', 'return_potential': '12-15%', 'liquidity': 'medium'},
                    {'name': 'PPF', 'lock_in': '15 years', 'return_potential': '7-8%', 'liquidity': 'low'},
                    {'name': 'NSC', 'lock_in': '5 years', 'return_potential': '6-7%', 'liquidity': 'low'},
                    {'name': 'Life Insurance Premium', 'lock_in': 'Policy term', 'return_potential': '4-6%', 'liquidity': 'low'},
                    {'name': 'Home Loan Principal', 'lock_in': 'Loan tenure', 'return_potential': 'Tax benefit', 'liquidity': 'low'},
                    {'name': 'ULIP', 'lock_in': '5 years', 'return_potential': '8-12%', 'liquidity': 'medium'}
                ],
                'description': 'Investment in specified savings schemes'
            },
            '80D': {
                'limit': 25000,  # For individual + family below 60
                'limit_senior': 50000,  # If individual or parents are senior citizens
                'options': [
                    {'name': 'Health Insurance Premium', 'coverage': 'Self + Family', 'benefit': 'Health coverage + tax saving'},
                    {'name': 'Preventive Health Check-up', 'limit': 5000, 'benefit': 'Early health detection'}
                ],
                'description': 'Medical insurance premiums and health check-ups'
            },
            '80CCD1B': {
                'limit': 50000,
                'options': [
                    {'name': 'NPS (National Pension System)', 'lock_in': 'Till 60 years', 'return_potential': '10-12%', 'benefit': 'Retirement corpus'}
                ],
                'description': 'Additional NPS contribution (over and above 80C)'
            },
            '80G': {
                'limit': 'Varies',
                'options': [
                    {'name': 'PM CARES Fund', 'deduction': '100%', 'limit': 'No limit'},
                    {'name': 'Charitable donations', 'deduction': '50% or 100%', 'limit': 'Varies by organization'}
                ],
                'description': 'Donations to specified funds and charitable institutions'
            }
        }
        
        # HRA calculation parameters
        self.hra_rules = {
            'metro_cities': ['Mumbai', 'Delhi', 'Chennai', 'Kolkata'],
            'metro_percentage': 50,  # 50% of basic salary in metro cities
            'non_metro_percentage': 40  # 40% of basic salary in non-metro cities
        }
    
    def calculate_tax_savings(self, annual_income, city='Mumbai', salary_breakdown=None, current_investments=None):
        """Calculate comprehensive tax savings and optimization"""
        
        # Default salary breakdown if not provided
        if not salary_breakdown:
            salary_breakdown = {
                'basic': annual_income * 0.50,
                'hra': annual_income * 0.20,
                'special_allowance': annual_income * 0.30,
                'city': city
            }
        
        # Current investments/deductions if not provided
        if not current_investments:
            current_investments = {
                '80C': 0,
                '80D': 0,
                '80CCD1B': 0,
                'HRA_claimed': 0
            }
        
        # Calculate tax for both regimes
        tax_old_regime = self.calculate_tax_old_regime(annual_income, current_investments, salary_breakdown)
        tax_new_regime = self.calculate_tax_new_regime(annual_income)
        
        # Determine better regime
        better_regime = 'new' if tax_new_regime['total_tax'] < tax_old_regime['total_tax'] else 'old'
        
        # Calculate optimization suggestions
        optimization_plan = self.generate_optimization_plan(annual_income, current_investments, salary_breakdown)
        
        return {
            'annual_income': annual_income,
            'old_regime': tax_old_regime,
            'new_regime': tax_new_regime,
            'recommended_regime': better_regime,
            'potential_savings': abs(tax_old_regime['total_tax'] - tax_new_regime['total_tax']),
            'current_investments': current_investments,
            'optimization_plan': optimization_plan,
            'monthly_savings_needed': optimization_plan['total_monthly_investment'],
            'summary': self.generate_tax_summary(tax_old_regime, tax_new_regime, better_regime)
        }
    
    def calculate_tax_old_regime(self, annual_income, investments, salary_breakdown):
        """Calculate tax under old regime with deductions"""
        
        # Calculate HRA exemption
        hra_exemption = self.calculate_hra_exemption(salary_breakdown)
        
        # Calculate total deductions
        deduction_80c = min(investments.get('80C', 0), self.deduction_sections['80C']['limit'])
        deduction_80d = min(investments.get('80D', 0), self.deduction_sections['80D']['limit'])
        deduction_80ccd1b = min(investments.get('80CCD1B', 0), self.deduction_sections['80CCD1B']['limit'])
        
        total_deductions = deduction_80c + deduction_80d + deduction_80ccd1b + hra_exemption
        
        # Calculate taxable income
        taxable_income = max(0, annual_income - total_deductions)
        
        # Calculate tax
        tax_amount = self.calculate_tax_from_slabs(taxable_income, self.tax_slabs['old_regime'])
        
        # Add cess (4% on tax amount)
        cess = tax_amount * 0.04
        total_tax = tax_amount + cess
        
        return {
            'gross_income': annual_income,
            'total_deductions': total_deductions,
            'deduction_breakdown': {
                '80C': deduction_80c,
                '80D': deduction_80d,
                '80CCD1B': deduction_80ccd1b,
                'HRA': hra_exemption
            },
            'taxable_income': taxable_income,
            'tax_before_cess': tax_amount,
            'cess': cess,
            'total_tax': total_tax,
            'effective_tax_rate': (total_tax / annual_income) * 100,
            'take_home_annual': annual_income - total_tax,
            'take_home_monthly': (annual_income - total_tax) / 12
        }
    
    def calculate_tax_new_regime(self, annual_income):
        """Calculate tax under new regime (no deductions except standard)"""
        
        # Standard deduction of 50,000
        standard_deduction = 50000
        taxable_income = max(0, annual_income - standard_deduction)
        
        # Calculate tax
        tax_amount = self.calculate_tax_from_slabs(taxable_income, self.tax_slabs['new_regime'])
        
        # Add cess (4% on tax amount)  
        cess = tax_amount * 0.04
        total_tax = tax_amount + cess
        
        return {
            'gross_income': annual_income,
            'standard_deduction': standard_deduction,
            'taxable_income': taxable_income,
            'tax_before_cess': tax_amount,
            'cess': cess,
            'total_tax': total_tax,
            'effective_tax_rate': (total_tax / annual_income) * 100,
            'take_home_annual': annual_income - total_tax,
            'take_home_monthly': (annual_income - total_tax) / 12
        }
    
    def calculate_tax_from_slabs(self, income, slabs):
        """Calculate tax from income slabs"""
        tax = 0
        remaining_income = income
        previous_limit = 0
        
        for limit, rate in slabs:
            if remaining_income <= 0:
                break
            
            taxable_in_slab = min(remaining_income, limit - previous_limit)
            tax += taxable_in_slab * rate
            remaining_income -= taxable_in_slab
            previous_limit = limit
            
        return tax
    
    def calculate_hra_exemption(self, salary_breakdown):
        """Calculate HRA exemption"""
        if not salary_breakdown.get('hra') or not salary_breakdown.get('basic'):
            return 0
        
        basic_salary = salary_breakdown['basic']
        hra_received = salary_breakdown['hra']
        city = salary_breakdown.get('city', 'Mumbai')
        rent_paid = salary_breakdown.get('rent_paid', hra_received)  # Assume rent = HRA if not specified
        
        # HRA exemption is minimum of:
        # 1. Actual HRA received
        # 2. 50% of basic (metro) or 40% of basic (non-metro)
        # 3. Rent paid - 10% of basic salary
        
        metro_percentage = self.hra_rules['metro_percentage'] if city in self.hra_rules['metro_cities'] else self.hra_rules['non_metro_percentage']
        
        exemption_options = [
            hra_received,
            basic_salary * (metro_percentage / 100),
            max(0, rent_paid - (basic_salary * 0.10))
        ]
        
        return min(exemption_options)
    
    def generate_optimization_plan(self, annual_income, current_investments, salary_breakdown):
        """Generate tax optimization plan"""
        
        optimization_suggestions = []
        total_monthly_investment = 0
        total_annual_savings = 0
        
        # 80C Optimization
        current_80c = current_investments.get('80C', 0)
        if current_80c < self.deduction_sections['80C']['limit']:
            remaining_80c = self.deduction_sections['80C']['limit'] - current_80c
            monthly_80c = remaining_80c / 12
            tax_saved = remaining_80c * self.get_tax_bracket(annual_income)
            
            optimization_suggestions.append({
                'section': '80C',
                'current_investment': current_80c,
                'recommended_additional': remaining_80c,
                'monthly_investment_needed': monthly_80c,
                'annual_tax_savings': tax_saved,
                'best_options': self.get_best_80c_options(annual_income),
                'priority': 'High'
            })
            
            total_monthly_investment += monthly_80c
            total_annual_savings += tax_saved
        
        # 80D Optimization
        current_80d = current_investments.get('80D', 0)
        if current_80d < self.deduction_sections['80D']['limit']:
            remaining_80d = self.deduction_sections['80D']['limit'] - current_80d
            monthly_80d = remaining_80d / 12
            tax_saved = remaining_80d * self.get_tax_bracket(annual_income)
            
            optimization_suggestions.append({
                'section': '80D',
                'current_investment': current_80d,
                'recommended_additional': remaining_80d,
                'monthly_investment_needed': monthly_80d,
                'annual_tax_savings': tax_saved,
                'best_options': ['Comprehensive Health Insurance', 'Family Floater Plan'],
                'priority': 'High'
            })
            
            total_monthly_investment += monthly_80d
            total_annual_savings += tax_saved
        
        # 80CCD1B Optimization (NPS)
        current_nps = current_investments.get('80CCD1B', 0)
        if current_nps < self.deduction_sections['80CCD1B']['limit']:
            remaining_nps = self.deduction_sections['80CCD1B']['limit'] - current_nps
            monthly_nps = remaining_nps / 12
            tax_saved = remaining_nps * self.get_tax_bracket(annual_income)
            
            optimization_suggestions.append({
                'section': '80CCD1B',
                'current_investment': current_nps,
                'recommended_additional': remaining_nps,
                'monthly_investment_needed': monthly_nps,
                'annual_tax_savings': tax_saved,
                'best_options': ['NPS Tier-I Account'],
                'priority': 'Medium'
            })
            
            total_monthly_investment += monthly_nps
            total_annual_savings += tax_saved
        
        return {
            'suggestions': optimization_suggestions,
            'total_monthly_investment': total_monthly_investment,
            'total_annual_tax_savings': total_annual_savings,
            'roi_on_tax_planning': (total_annual_savings / (total_monthly_investment * 12)) * 100 if total_monthly_investment > 0 else 0,
            'implementation_timeline': self.generate_implementation_timeline(optimization_suggestions)
        }
    
    def get_tax_bracket(self, annual_income):
        """Get marginal tax rate for the income"""
        if annual_income <= 500000:
            return 0.05
        elif annual_income <= 1000000:
            return 0.20
        else:
            return 0.30
    
    def get_best_80c_options(self, annual_income):
        """Get best 80C options based on income level"""
        if annual_income < 600000:  # Lower income
            return [
                {'option': 'PPF', 'allocation': 60, 'reason': 'Safe, guaranteed returns'},
                {'option': 'ELSS', 'allocation': 40, 'reason': 'Growth potential, shorter lock-in'}
            ]
        elif annual_income < 1500000:  # Middle income
            return [
                {'option': 'ELSS', 'allocation': 60, 'reason': 'Best returns, liquidity after 3 years'},
                {'option': 'PPF', 'allocation': 30, 'reason': 'Debt allocation, tax-free returns'},
                {'option': 'Life Insurance', 'allocation': 10, 'reason': 'Life cover essential'}
            ]
        else:  # Higher income
            return [
                {'option': 'ELSS', 'allocation': 70, 'reason': 'Maximum wealth creation'},
                {'option': 'PPF', 'allocation': 20, 'reason': 'Stability in portfolio'},
                {'option': 'NPS', 'allocation': 10, 'reason': 'Additional retirement corpus'}
            ]
    
    def generate_implementation_timeline(self, suggestions):
        """Generate month-by-month implementation timeline"""
        timeline = []
        
        # Sort by priority
        high_priority = [s for s in suggestions if s['priority'] == 'High']
        medium_priority = [s for s in suggestions if s['priority'] == 'Medium']
        
        month = 1
        for suggestion in high_priority + medium_priority:
            timeline.append({
                'month': month,
                'action': f"Start {suggestion['section']} investments",
                'amount': suggestion['monthly_investment_needed'],
                'specific_steps': self.get_implementation_steps(suggestion['section'])
            })
            month += 1
        
        return timeline
    
    def get_implementation_steps(self, section):
        """Get specific implementation steps for each section"""
        steps = {
            '80C': [
                "Open ELSS mutual fund account online",
                "Start PPF account at bank/post office",
                "Set up monthly SIP for chosen amount",
                "Keep investment proofs for ITR filing"
            ],
            '80D': [
                "Compare health insurance policies online",
                "Choose family floater plan with adequate coverage",
                "Complete medical check-ups if required",
                "Pay premium and collect policy documents"
            ],
            '80CCD1B': [
                "Open NPS account online or through bank",
                "Choose investment mix based on age",
                "Set up auto-debit for monthly contributions",
                "Monitor fund performance regularly"
            ]
        }
        
        return steps.get(section, ["Consult financial advisor for specific steps"])
    
    def generate_tax_summary(self, old_regime_tax, new_regime_tax, recommended):
        """Generate executive summary of tax analysis"""
        savings_amount = abs(old_regime_tax['total_tax'] - new_regime_tax['total_tax'])
        
        return {
            'regime_recommendation': recommended,
            'annual_tax_savings': savings_amount,
            'monthly_tax_savings': savings_amount / 12,
            'key_insights': [
                f"You can save ₹{savings_amount:,.0f} annually by choosing {recommended} regime",
                f"Effective tax rate: {old_regime_tax['effective_tax_rate']:.1f}% (old) vs {new_regime_tax['effective_tax_rate']:.1f}% (new)",
                f"Take-home monthly: ₹{old_regime_tax['take_home_monthly']:,.0f} (old) vs ₹{new_regime_tax['take_home_monthly']:,.0f} (new)"
            ],
            'next_steps': [
                "Review current tax-saving investments",
                "Implement recommended optimization plan",
                "Set up monthly SIPs for tax-saving instruments",
                "Consult CA for detailed tax planning"
            ]
        }
    
    def calculate_advance_tax(self, annual_income, quarterly=True):
        """Calculate advance tax liability"""
        # This is a simplified calculation
        total_tax = self.calculate_tax_new_regime(annual_income)['total_tax']
        
        if quarterly:
            return {
                'Q1 (by June 15)': total_tax * 0.15,
                'Q2 (by Sep 15)': total_tax * 0.30,  # 45% - 15%
                'Q3 (by Dec 15)': total_tax * 0.30,  # 75% - 45%
                'Q4 (by Mar 15)': total_tax * 0.25   # 100% - 75%
            }
        else:
            return {'Annual advance tax': total_tax}
