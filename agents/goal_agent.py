import math
from datetime import datetime, timedelta

class GoalAgent:
    def __init__(self):
        # Predefined goal categories with typical costs and time horizons
        self.goal_templates = {
            'emergency_fund': {
                'typical_amount': lambda income: income * 6,  # 6 months of expenses
                'time_horizon': 1,  # 1 year to build
                'priority': 'critical',
                'investment_type': 'liquid',
                'expected_return': 5
            },
            'house_purchase': {
                'typical_amount': lambda income: income * 60,  # 5 years of income as down payment
                'time_horizon': 7,
                'priority': 'high',
                'investment_type': 'hybrid',
                'expected_return': 10
            },
            'car_purchase': {
                'typical_amount': lambda income: income * 8,  # ~8 months income
                'time_horizon': 3,
                'priority': 'medium',
                'investment_type': 'conservative',
                'expected_return': 8
            },
            'marriage': {
                'typical_amount': lambda income: income * 20,  # ~20 months income
                'time_horizon': 4,
                'priority': 'high',
                'investment_type': 'moderate',
                'expected_return': 9
            },
            'education': {
                'typical_amount': lambda income: income * 36,  # 3 years income for higher education
                'time_horizon': 5,
                'priority': 'high',
                'investment_type': 'moderate',
                'expected_return': 11
            },
            'retirement': {
                'typical_amount': lambda income: income * 300,  # 25 years of expenses
                'time_horizon': 25,
                'priority': 'critical',
                'investment_type': 'aggressive',
                'expected_return': 12
            },
            'vacation': {
                'typical_amount': lambda income: income * 2,  # 2 months income
                'time_horizon': 1,
                'priority': 'low',
                'investment_type': 'liquid',
                'expected_return': 6
            },
            'child_education': {
                'typical_amount': lambda income: income * 60,  # Higher education corpus
                'time_horizon': 15,
                'priority': 'critical',
                'investment_type': 'aggressive',
                'expected_return': 12
            }
        }
        
        # Investment recommendations based on time horizon
        self.investment_recommendations = {
            'liquid': {  # 0-2 years
                'allocation': {'liquid': 80, 'debt': 20, 'equity': 0},
                'instruments': ['Liquid Funds', 'Ultra Short Duration Funds', 'Savings Account'],
                'risk_level': 'Very Low'
            },
            'conservative': {  # 2-5 years
                'allocation': {'liquid': 20, 'debt': 60, 'equity': 20},
                'instruments': ['Short Duration Funds', 'Conservative Hybrid Funds', 'FD'],
                'risk_level': 'Low'
            },
            'moderate': {  # 3-7 years
                'allocation': {'liquid': 10, 'debt': 40, 'equity': 50},
                'instruments': ['Balanced Advantage Funds', 'Hybrid Funds', 'Large Cap Funds'],
                'risk_level': 'Moderate'
            },
            'hybrid': {  # 5-10 years
                'allocation': {'liquid': 5, 'debt': 25, 'equity': 70},
                'instruments': ['Multi Cap Funds', 'Large & Mid Cap Funds', 'Debt Funds'],
                'risk_level': 'Moderate to High'
            },
            'aggressive': {  # 10+ years
                'allocation': {'liquid': 5, 'debt': 15, 'equity': 80},
                'instruments': ['Mid Cap Funds', 'Small Cap Funds', 'Multi Cap Funds'],
                'risk_level': 'High'
            }
        }
    
    def analyze_goals(self, user_goals, monthly_income, current_savings=0):
        """Analyze user goals and provide SIP recommendations"""
        
        if not user_goals:
            return self.generate_default_goals(monthly_income)
        
        analyzed_goals = []
        total_monthly_sip_needed = 0
        goal_priorities = {'critical': [], 'high': [], 'medium': [], 'low': []}
        
        for goal in user_goals:
            goal_analysis = self.analyze_single_goal(goal, monthly_income, current_savings)
            analyzed_goals.append(goal_analysis)
            total_monthly_sip_needed += goal_analysis['monthly_sip_required']
            
            # Categorize by priority
            priority = goal_analysis['priority']
            goal_priorities[priority].append(goal_analysis)
        
        # Generate recommendations based on income capacity
        recommendations = self.generate_goal_recommendations(
            analyzed_goals, 
            monthly_income, 
            total_monthly_sip_needed
        )
        
        return {
            'goals': analyzed_goals,
            'total_monthly_sip_needed': total_monthly_sip_needed,
            'income_allocation_percentage': (total_monthly_sip_needed / monthly_income) * 100,
            'goal_priorities': goal_priorities,
            'recommendations': recommendations,
            'feasibility_analysis': self.assess_feasibility(total_monthly_sip_needed, monthly_income),
            'optimization_suggestions': self.optimize_goals(analyzed_goals, monthly_income)
        }
    
    def analyze_single_goal(self, goal, monthly_income, current_savings=0):
        """Analyze a single financial goal"""
        
        goal_name = goal.get('name', 'Custom Goal').lower()
        target_amount = goal.get('amount', 0)
        time_horizon = goal.get('time_years', 5)
        current_corpus = goal.get('current_savings', current_savings)
        
        # Get goal template if available
        template = None
        for template_name, template_data in self.goal_templates.items():
            if template_name in goal_name or goal_name in template_name:
                template = template_data
                break
        
        # Use template defaults if goal amount not specified
        if not target_amount and template:
            target_amount = template['typical_amount'](monthly_income)
        
        # Determine investment strategy based on time horizon
        investment_type = self.determine_investment_strategy(time_horizon, template)
        expected_return = self.get_expected_return(investment_type, time_horizon)
        
        # Calculate SIP requirements
        remaining_amount = max(0, target_amount - current_corpus)
        
        if time_horizon <= 0:
            monthly_sip = remaining_amount  # Immediate goal
            future_value_with_growth = remaining_amount
        else:
            monthly_sip = self.calculate_sip_amount(remaining_amount, expected_return, time_horizon)
            future_value_with_growth = self.calculate_future_value(monthly_sip, expected_return, time_horizon) + current_corpus
        
        # Calculate corpus growth if no additional investment
        corpus_future_value = current_corpus * ((1 + expected_return/100) ** time_horizon) if current_corpus > 0 else 0
        
        return {
            'name': goal.get('name', 'Custom Goal'),
            'target_amount': target_amount,
            'time_horizon_years': time_horizon,
            'current_corpus': current_corpus,
            'remaining_amount': remaining_amount,
            'monthly_sip_required': monthly_sip,
            'total_investment_needed': monthly_sip * 12 * time_horizon,
            'expected_return': expected_return,
            'future_value_projection': future_value_with_growth,
            'corpus_growth_without_sip': corpus_future_value,
            'investment_strategy': investment_type,
            'recommended_instruments': self.investment_recommendations[investment_type]['instruments'],
            'asset_allocation': self.investment_recommendations[investment_type]['allocation'],
            'risk_level': self.investment_recommendations[investment_type]['risk_level'],
            'priority': template['priority'] if template else 'medium',
            'goal_category': self.categorize_goal(goal_name),
            'inflation_adjusted_target': self.adjust_for_inflation(target_amount, time_horizon),
            'feasibility_score': self.calculate_feasibility_score(monthly_sip, monthly_income),
            'milestone_tracking': self.generate_milestones(target_amount, time_horizon)
        }
    
    def generate_goal_recommendations(self, analyzed_goals, monthly_income, total_monthly_sip_needed):
        """Generate recommendations based on analyzed goals"""
        recommendations = []
        
        # Calculate affordability
        affordable_sip = monthly_income * 0.25  # 25% of income max recommended for goals
        sip_percentage = (total_monthly_sip_needed / monthly_income) * 100
        
        # Income-based recommendations
        if monthly_income < 30000:
            recommendations.extend([
                "Focus on building emergency fund first (₹1-2 lakhs)",
                "Start with small SIPs of ₹1,000-2,000 per month",
                "Prefer conservative investments like PPF and debt funds",
                "Avoid too many goals initially - prioritize 2-3 essential ones"
            ])
        elif monthly_income < 75000:
            recommendations.extend([
                "Build emergency fund of ₹3-4 lakhs in liquid funds",
                "Allocate ₹5,000-10,000 monthly for goal-based investing",
                "Balance between debt and equity funds (40:60 ratio)",
                "Consider ELSS funds for tax saving + goal achievement"
            ])
        else:
            recommendations.extend([
                "Maintain robust emergency fund of ₹6-8 lakhs",
                "Can afford ₹15,000+ monthly SIPs for multiple goals",
                "Aggressive portfolio allocation (70% equity, 30% debt)",
                "Consider real estate and alternative investments"
            ])
        
        # Goal prioritization recommendations
        critical_goals = [g for g in analyzed_goals if g.get('priority') == 'critical']
        high_goals = [g for g in analyzed_goals if g.get('priority') == 'high']
        
        if len(critical_goals) > 3:
            recommendations.append("You have too many critical goals. Consider extending timelines for some goals.")
        
        if len(analyzed_goals) > 5:
            recommendations.append("Consider consolidating similar goals or extending timelines to reduce monthly SIP burden.")
        
        # SIP affordability recommendations
        if sip_percentage > 30:
            recommendations.extend([
                "Current goals require too much of your income (>30%)",
                "Consider extending goal timelines by 1-2 years",
                "Focus on increasing income through skill development",
                "Defer low-priority goals until income increases"
            ])
        elif sip_percentage > 20:
            recommendations.extend([
                "Goals are stretching your budget (>20% of income)",
                "Monitor expenses closely to ensure SIP sustainability",
                "Consider automated investing to maintain discipline"
            ])
        else:
            recommendations.extend([
                "Your goals are well within affordable limits",
                "Consider adding more ambitious goals or increasing SIP amounts",
                "You have room for additional investments like NPS or real estate"
            ])
        
        # Time horizon recommendations
        short_term_goals = [g for g in analyzed_goals if g.get('time_horizon_years', 0) < 3]
        long_term_goals = [g for g in analyzed_goals if g.get('time_horizon_years', 0) > 10]
        
        if len(short_term_goals) > 2:
            recommendations.append("Multiple short-term goals detected. Keep funds in liquid/debt instruments.")
        
        if len(long_term_goals) > 0:
            recommendations.append("For long-term goals (10+ years), maximize equity allocation for better returns.")
        
        # Investment strategy recommendations
        recommendations.extend([
            "Review and rebalance your portfolio annually",
            "Increase SIP amount by 10-15% each year with salary increments",
            "Don't panic during market downturns - stay invested for long-term goals",
            "Consider goal-based mutual funds for automated management"
        ])
        
        return {
            'general_recommendations': recommendations,
            'affordability_score': min(100, max(0, 100 - (sip_percentage - 15) * 5)),
            'priority_adjustment_needed': len(critical_goals) > 3 or sip_percentage > 25,
            'suggested_max_monthly_sip': affordable_sip,
            'current_monthly_sip': total_monthly_sip_needed,
            'income_utilization_percentage': round(sip_percentage, 1),
            'recommended_emergency_fund': monthly_income * 6,
            'investment_horizon_advice': {
                'short_term': "Use liquid funds and short-duration debt funds",
                'medium_term': "Balanced advantage funds and conservative hybrid funds", 
                'long_term': "Equity mutual funds with 70-80% allocation"
            }
        }
    
    def determine_investment_strategy(self, time_horizon, template):
        """Determine investment strategy based on time horizon"""
        if template and 'investment_type' in template:
            return template['investment_type']
        
        if time_horizon <= 2:
            return 'liquid'
        elif time_horizon <= 5:
            return 'conservative'
        elif time_horizon <= 10:
            return 'moderate'
        else:
            return 'aggressive'
    
    def get_expected_return(self, investment_type, time_horizon):
        """Get expected return based on investment strategy"""
        base_returns = {
            'liquid': 5,
            'conservative': 7,
            'moderate': 9,
            'hybrid': 10,
            'aggressive': 12
        }
        
        base_return = base_returns.get(investment_type, 8)
        
        # Adjust for time horizon (longer horizon, slightly higher returns due to compounding)
        if time_horizon > 10:
            base_return += 1
        elif time_horizon < 2:
            base_return -= 1
        
        return base_return
    
    def calculate_sip_amount(self, target_amount, annual_return, years):
        """Calculate monthly SIP required for target amount"""
        if annual_return <= 0 or years <= 0:
            return target_amount / (years * 12) if years > 0 else target_amount
        
        monthly_return = annual_return / 12 / 100
        months = years * 12
        
        # SIP formula: P = FV * r / ((1+r)^n - 1)
        sip_amount = target_amount * monthly_return / (((1 + monthly_return) ** months) - 1)
        
        return round(sip_amount, 2)
    
    def calculate_future_value(self, monthly_sip, annual_return, years):
        """Calculate future value of SIP"""
        if annual_return <= 0 or years <= 0:
            return monthly_sip * 12 * years
        
        monthly_return = annual_return / 12 / 100
        months = years * 12
        
        # FV = P * (((1+r)^n - 1) / r) * (1+r)
        future_value = monthly_sip * (((1 + monthly_return) ** months - 1) / monthly_return) * (1 + monthly_return)
        
        return round(future_value, 2)
    
    def adjust_for_inflation(self, amount, years, inflation_rate=6):
        """Adjust target amount for inflation"""
        return round(amount * ((1 + inflation_rate/100) ** years), 2)
    
    def calculate_feasibility_score(self, monthly_sip, monthly_income):
        """Calculate feasibility score (0-100)"""
        sip_percentage = (monthly_sip / monthly_income) * 100
        
        if sip_percentage <= 5:
            return 100
        elif sip_percentage <= 10:
            return 80
        elif sip_percentage <= 15:
            return 60
        elif sip_percentage <= 20:
            return 40
        elif sip_percentage <= 25:
            return 20
        else:
            return 0
    
    def categorize_goal(self, goal_name):
        """Categorize goal into standard categories"""
        categories = {
            'wealth': ['retirement', 'investment', 'corpus'],
            'lifestyle': ['car', 'bike', 'vacation', 'travel'],
            'property': ['house', 'home', 'property', 'flat'],
            'family': ['marriage', 'wedding', 'child', 'education'],
            'security': ['emergency', 'insurance', 'health']
        }
        
        for category, keywords in categories.items():
            if any(keyword in goal_name for keyword in keywords):
                return category
        
        return 'other'
    
    def generate_milestones(self, target_amount, years):
        """Generate milestone tracking for goals"""
        milestones = []
        
        if years <= 1:
            quarters = max(1, int(years * 4))
            for i in range(1, quarters + 1):
                milestone_amount = (target_amount * i) / quarters
                milestone_date = datetime.now() + timedelta(days=90*i)
                milestones.append({
                    'milestone': f'Quarter {i}',
                    'target_amount': round(milestone_amount, 2),
                    'target_date': milestone_date.strftime('%B %Y'),
                    'percentage': (i * 100) / quarters
                })
        else:
            for i in range(1, min(int(years) + 1, 6)):  # Max 5 milestones
                milestone_amount = (target_amount * i) / years
                milestone_date = datetime.now() + timedelta(days=365*i)
                milestones.append({
                    'milestone': f'Year {i}',
                    'target_amount': round(milestone_amount, 2),
                    'target_date': milestone_date.strftime('%B %Y'),
                    'percentage': (i * 100) / years
                })
        
        return milestones
    
    def assess_feasibility(self, total_sip_needed, monthly_income):
        """Assess overall feasibility of all goals"""
        sip_percentage = (total_sip_needed / monthly_income) * 100
        
        if sip_percentage <= 15:
            status = "Highly Feasible"
            message = "Your goals are well within your income capacity. Great planning!"
        elif sip_percentage <= 25:
            status = "Feasible with Discipline"
            message = "Your goals are achievable with disciplined saving and expense management."
        elif sip_percentage <= 35:
            status = "Challenging but Possible"
            message = "Consider prioritizing goals or extending timelines for better feasibility."
        else:
            status = "Needs Restructuring"
            message = "Current goals exceed recommended savings rate. Prioritization is essential."
        
        return {
            'status': status,
            'sip_percentage_of_income': sip_percentage,
            'message': message,
            'recommended_max_sip': monthly_income * 0.25,  # 25% of income
            'excess_amount': max(0, total_sip_needed - (monthly_income * 0.25))
        }
    
    def optimize_goals(self, goals, monthly_income):
        """Suggest optimizations for better goal achievement"""
        suggestions = []
        max_recommended_sip = monthly_income * 0.25
        
        # Sort goals by priority and feasibility
        high_priority_goals = [g for g in goals if g['priority'] in ['critical', 'high']]
        total_high_priority_sip = sum(g['monthly_sip_required'] for g in high_priority_goals)
        
        if total_high_priority_sip > max_recommended_sip:
            suggestions.append({
                'type': 'prioritization',
                'message': 'Focus on critical and high-priority goals first',
                'action': 'Consider deferring medium and low priority goals'
            })
        
        # Check for goals with poor feasibility scores
        difficult_goals = [g for g in goals if g['feasibility_score'] < 60]
        for goal in difficult_goals:
            suggestions.append({
                'type': 'timeline_extension',
                'goal': goal['name'],
                'current_timeline': goal['time_horizon_years'],
                'suggested_timeline': goal['time_horizon_years'] + 2,
                'new_sip': self.calculate_sip_amount(
                    goal['remaining_amount'], 
                    goal['expected_return'], 
                    goal['time_horizon_years'] + 2
                ),
                'message': f"Extend timeline by 2 years to reduce monthly SIP burden"
            })
        
        # Income increase suggestions
        if sum(g['monthly_sip_required'] for g in goals) > max_recommended_sip:
            suggestions.append({
                'type': 'income_enhancement',
                'message': 'Consider increasing income through skill development or side income',
                'target_increase': sum(g['monthly_sip_required'] for g in goals) - max_recommended_sip
            })
        
        return suggestions
    
    def generate_default_goals(self, monthly_income):
        """Generate default goals based on income level"""
        default_goals = []
        
        # Always recommend emergency fund
        default_goals.append({
            'name': 'Emergency Fund',
            'amount': monthly_income * 6,
            'time_years': 2,
            'current_savings': 0
        })
        
        # Income-based recommendations
        if monthly_income >= 50000:
            default_goals.append({
                'name': 'House Purchase',
                'amount': monthly_income * 60,
                'time_years': 10,
                'current_savings': 0
            })
        
        if monthly_income >= 30000:
            default_goals.append({
                'name': 'Car Purchase', 
                'amount': monthly_income * 8,
                'time_years': 5,
                'current_savings': 0
            })
        
        # Always recommend retirement planning
        default_goals.append({
            'name': 'Retirement Corpus',
            'amount': monthly_income * 300,
            'time_years': 25,
            'current_savings': 0
        })
        
        return self.analyze_goals(default_goals, monthly_income)
    
    def generate_sip_schedule(self, goals):
        """Generate a monthly SIP schedule across all goals"""
        schedule = {}
        total_monthly_sip = 0
        
        for goal in goals:
            if goal['monthly_sip_required'] > 0:
                schedule[goal['name']] = {
                    'monthly_amount': goal['monthly_sip_required'],
                    'recommended_date': 5,  # 5th of every month
                    'investment_instruments': goal['recommended_instruments'][:2],  # Top 2 instruments
                    'auto_debit_setup': True
                }
                total_monthly_sip += goal['monthly_sip_required']
        
        schedule['total_monthly_commitment'] = total_monthly_sip
        schedule['suggested_sip_dates'] = [5, 15, 25]  # Spread across month
        
        return schedule
