import os
import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WorkingChatbot:
    """Chatbot that uses your OpenRouter API"""
    
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')
        
        logger.info(f"Chatbot initialized with OpenRouter: {'✓' if self.openrouter_key else '✗'}")
        logger.info(f"Using model: {self.openrouter_model}")
    
    def get_contextual_response(self, message, user_context):
        """Get contextual response using OpenRouter API"""
        try:
            # If OpenRouter API is available, use it
            if self.openrouter_key:
                return self._get_openrouter_response(message, user_context)
            else:
                return self._get_rule_based_response(message, user_context)
                
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return self._get_rule_based_response(message, user_context)
    
    def _get_openrouter_response(self, message, context):
        """Get response from OpenRouter API"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            # Build context prompt
            context_prompt = self._build_context_prompt(context)
            
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "MoneyMentor"
            }
            
            system_prompt = f"""You are MoneyMentor, a friendly Indian financial advisor chatbot. 
Help users with money management in simple, practical language that Indians understand.

User's Financial Context:
{context_prompt}

Guidelines:
- Use simple language mixing English and common Hindi financial terms
- Give specific advice with exact amounts in ₹ (Rupees) 
- Be encouraging and supportive
- Focus on practical steps they can take immediately
- Keep responses under 150 words
- If they ask about investments, suggest realistic options based on their income and risk appetite
- Always mention emergency fund importance
- Use emojis to make responses friendly"""
            
            data = {
                "model": self.openrouter_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    logger.warning("No choices in OpenRouter response")
                    return self._get_rule_based_response(message, context)
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return self._get_rule_based_response(message, context)
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return self._get_rule_based_response(message, context)
    
    def _build_context_prompt(self, context):
        """Build context prompt from user's financial data"""
        if not context:
            return "User hasn't set up their financial plan yet."
        
        income = context.get('income', 0)
        risk = context.get('risk', 'moderate')
        plan_generated = context.get('planGenerated', False)
        goals_count = context.get('goals', 0)
        
        prompt = f"""
Monthly Income: ₹{income:,}
Risk Appetite: {risk}
Financial Plan: {'Generated' if plan_generated else 'Not set up'}
Goals Count: {goals_count}
"""
        
        if context.get('budget'):
            budget = context['budget']
            prompt += f"""
Budget Allocation:
- Essential Expenses: ₹{budget.get('needs', 0):,}
- Lifestyle Expenses: ₹{budget.get('wants', 0):,}
- Savings & Investments: ₹{budget.get('savings', 0):,}
"""
        
        return prompt
    
    def _get_rule_based_response(self, message, context):
        """Enhanced rule-based responses when API is not available"""
        message_lower = message.lower()
        
        # Extract user context
        income = context.get('income', 0) if context else 0
        risk = context.get('risk', 'moderate') if context else 'moderate'
        plan_generated = context.get('planGenerated', False) if context else False
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste', 'start']):
            if plan_generated:
                return f"🙏 Hello! I can see you earn ₹{income:,} monthly with {risk} risk appetite. How can I help you with your finances today? I can assist with budgeting, investments, goals, or any money questions! 💰"
            else:
                return "🙏 Namaste! I'm your MoneyMentor AI assistant. Please set up your financial plan first by entering your monthly income above, then I can give you personalized advice! Let's make your money work for you! 🚀"
        
        # Budget related queries
        if any(word in message_lower for word in ['budget', 'expenses', 'spending', 'allocation']):
            if plan_generated and income > 0:
                if income <= 50000:
                    return f"💡 For your ₹{income:,} income: Focus on 65% essentials (₹{income*0.65:,.0f}), 20% fun (₹{income*0.20:,.0f}), 15% savings (₹{income*0.15:,.0f}). Start small but start today! Build emergency fund of ₹{income*3:,.0f} first. 🎯"
                elif income <= 200000:
                    return f"📊 Perfect income for balanced planning! Allocate: 50% needs (₹{income*0.50:,.0f}), 30% wants (₹{income*0.30:,.0f}), 20% savings (₹{income*0.20:,.0f}). You can start SIPs of ₹{income*0.15:,.0f}/month easily! 💪"
                else:
                    return f"🔥 Great income! You can be aggressive: 40% needs (₹{income*0.40:,.0f}), 35% lifestyle (₹{income*0.35:,.0f}), 25% investments (₹{income*0.25:,.0f}). Target ₹{income*0.20:,.0f}/month in equity SIPs for wealth building! 📈"
            else:
                return "📋 I'd love to help with your budget! Please first enter your monthly income above and click 'Create My Plan', then I can give you a personalized budget breakdown based on your income level. 🎯"
        
        # Investment related queries  
        if any(word in message_lower for word in ['investment', 'invest', 'mutual fund', 'sip', 'stocks', 'returns']):
            if plan_generated and income > 0:
                if risk == 'conservative':
                    return f"🛡️ For safe investing with ₹{income:,} income: Start with ₹{min(income*0.10, 10000):,.0f}/month SIP in large-cap funds + debt funds. Try HDFC Top 100 or SBI Bluechip. Target 8-10% annual returns. Safety first! 🏦"
                elif risk == 'aggressive':
                    return f"🚀 For aggressive wealth building: Invest ₹{min(income*0.20, 25000):,.0f}/month in small-cap + mid-cap funds. Consider Axis Small Cap, SBI Small Cap. Expect 12-15% returns but with volatility. Stay invested 5+ years! 📊"
                else:  # moderate
                    return f"⚖️ Balanced approach perfect! Invest ₹{min(income*0.15, 20000):,.0f}/month: 60% equity funds (Axis Bluechip, Mirae Large Cap), 40% debt funds. Target 10-12% returns. Best of both worlds! 🎯"
            else:
                return "💰 I can suggest the best investments for you! Please set up your financial plan first by entering your income and risk preference above. Then I'll recommend specific funds and SIP amounts! 📈"
        
        # Goal related queries
        if any(word in message_lower for word in ['goal', 'target', 'house', 'car', 'marriage', 'retirement', 'planning']):
            if income > 0:
                return f"🎯 Great that you're thinking about goals! With ₹{income:,} income, you can plan for: House (7-10 years), Car (3-5 years), Retirement (start now!). For each ₹10 lakh goal in 5 years, you need ₹13,000/month SIP. Add goals above and I'll calculate exact amounts! 🏠🚗"
            else:
                return "🎯 Goals are super important for financial success! Common goals: Emergency fund → House → Car → Retirement. Set up your income first, then add specific goals with amounts and timelines. I'll calculate the exact monthly SIP needed! 📊"
        
        # Emergency fund queries
        if any(word in message_lower for word in ['emergency', 'emergency fund', 'backup', 'safe money']):
            if income > 0:
                emergency_amount = income * 6
                monthly_save = min(income * 0.05, emergency_amount / 24)
                return f"🚨 Emergency fund is crucial! Target: ₹{emergency_amount:,} (6 months expenses). Save ₹{monthly_save:,.0f}/month in savings account or liquid funds. Don't invest emergency money in stocks! Keep it easily accessible. 🏦💡"
            else:
                return "🚨 Emergency fund = your financial safety net! Should cover 6 months of expenses. Keep in savings account or liquid mutual funds for instant access. Never invest emergency money in risky assets! Set up your income to get specific targets. 🛡️"
        
        # Tax related queries
        if any(word in message_lower for word in ['tax', '80c', 'tax saving', 'deduction', 'elss']):
            if income > 0:
                if income > 250000:  # Above tax limit
                    tax_save_potential = min(income * 0.30, 46800)  # Max tax savings
                    return f"💸 Tax saving opportunity! With ₹{income:,} income: Invest ₹1.5L in ELSS funds (80C), ₹25K health insurance (80D). Potential tax savings: ₹{tax_save_potential:,.0f}! ELSS gives dual benefit - tax saving + wealth creation! 📋"
                else:
                    return f"😊 Good news! With ₹{income:,} income, you're in no-tax bracket. Focus on wealth building through SIPs rather than tax-saving investments. Start with regular mutual funds for better growth! 💪"
            else:
                return "📋 Tax planning depends on your income bracket. Set up your financial plan first, then I can suggest the best tax-saving investments like ELSS, PPF, health insurance based on your tax liability! 💰"
        
        # Savings queries
        if any(word in message_lower for word in ['save', 'savings', 'money', 'paisa']):
            if plan_generated and income > 0:
                savings_amount = income * (0.15 if income <= 50000 else 0.20 if income <= 200000 else 0.25)
                return f"💰 Your recommended monthly savings: ₹{savings_amount:,.0f}. Split this: 80% for SIP investments (₹{savings_amount*0.8:,.0f}), 20% for emergency fund (₹{savings_amount*0.2:,.0f}). Automate both to ensure consistency! Paisa saved = paisa earned! 🎯"
            else:
                return "💰 Smart saving = smart future! Generally save 15-25% of income. Higher income = higher savings rate. Set up your financial plan above and I'll show you exactly how much to save and where to invest it for maximum growth! 📈"
        
        # SIP/Monthly investment queries
        if any(word in message_lower for word in ['sip', 'monthly', 'systematic', 'regular investment']):
            if income > 0:
                suggested_sip = min(income * 0.15, 20000)
                return f"📅 SIP is the best way to build wealth! With your income, start with ₹{suggested_sip:,.0f}/month. Choose 5th or 10th of every month for auto-debit. Even ₹1000/month for 10 years = ₹2.3 lakhs (at 12% return)! Consistency beats timing! ⏰💪"
            else:
                return "📅 SIP (Systematic Investment Plan) = regular monthly investment in mutual funds. Best way to build wealth! Even ₹500/month helps. Start small, increase gradually. Set up your income first for personalized SIP recommendations! 🚀"
        
        # Market/volatility queries
        if any(word in message_lower for word in ['market', 'crash', 'down', 'loss', 'volatile', 'risk']):
            return "📊 Markets go up and down - that's normal! Key rules: 1) Never panic sell during crashes 2) SIP continues in all markets 3) Long-term (5+ years) investors always win 4) Emergency fund keeps you stress-free. Stay invested, stay patient! 💪🏼"
        
        # Default helpful response with income-based advice
        if income > 0:
            return f"🤖 I'm here to help with your finances! With ₹{income:,} monthly income, I can guide you on budgeting, investments, goal planning, tax savings, and more. What specific area would you like to discuss? Ask me anything about money! 💰"
        else:
            return "🤖 I'm your MoneyMentor AI assistant! I can help with budgeting, SIP investments, goal planning, tax savings, emergency funds, and all money matters. Set up your financial plan first by entering your income above for personalized advice! 🚀"

# Global instance
working_chatbot = WorkingChatbot()
