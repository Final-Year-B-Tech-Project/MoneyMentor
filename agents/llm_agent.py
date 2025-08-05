import requests
import json
import os
from datetime import datetime

class LLMAgent:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY', 'your-openrouter-api-key')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.environ.get('OPENROUTER_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')
        
        # Fallback responses for when API is unavailable
        self.fallback_responses = {
            'tax': {
                'keywords': ['tax', '80c', '80d', 'deduction', 'save tax', 'tax saving'],
                'response': """**Tax Saving Tips for Indians:**

🔹 **Section 80C (₹1.5L limit):** ELSS, PPF, Life Insurance, Home Loan Principal
🔹 **Section 80D (₹25K limit):** Health Insurance Premiums  
🔹 **HRA Exemption:** If you pay rent, claim HRA
🔹 **NPS (₹50K additional):** Extra deduction under 80CCD(1B)

**Recommended:** Start with ELSS funds - they offer tax savings + market returns!"""
            },
            'investment': {
                'keywords': ['invest', 'mutual fund', 'sip', 'portfolio', 'equity', 'debt'],
                'response': """**Smart Investment Strategy for Indians:**

🔹 **Emergency Fund First:** 6 months expenses in liquid funds
🔹 **Equity (60-70%):** Large Cap + Mid Cap + ELSS funds
🔹 **Debt (20-30%):** PPF, Corporate Bonds, Debt Funds  
🔹 **Gold (5-10%):** Gold ETF or Digital Gold

**SIP Approach:** Start with ₹5,000/month across 3-4 good funds. Increase by 10% annually."""
            },
            'budget': {
                'keywords': ['budget', '50/30/20', 'expense', 'spending', 'save money'],
                'response': """**50/30/20 Budget Rule:**

🔹 **50% Needs:** Rent, Groceries, Utilities, EMIs
🔹 **30% Wants:** Entertainment, Dining, Shopping  
🔹 **20% Savings:** SIP, PPF, Emergency Fund

**Tips:** Track expenses using apps, automate savings, review monthly!"""
            },
            'goal': {
                'keywords': ['goal', 'house', 'car', 'marriage', 'vacation', 'planning'],
                'response': """**Goal-Based Planning:**

🔹 **Short-term (1-3 years):** Liquid funds, Short duration funds
🔹 **Medium-term (3-7 years):** Hybrid funds, Conservative portfolio
🔹 **Long-term (7+ years):** Equity-heavy portfolio

**Formula:** Required Amount ÷ Number of months = Monthly SIP needed"""
            }
        }
    
    def get_response(self, user_message, user_income=None, user_context=None):
        """Get AI response for financial queries"""
        
        # Create context-aware system prompt
        system_prompt = self.create_system_prompt(user_income, user_context)
        
        # Try API call first
        api_response = self.call_openrouter_api(system_prompt, user_message)
        
        if api_response:
            return api_response
        
        # Fall back to predefined responses
        return self.get_fallback_response(user_message)
    
    def create_system_prompt(self, user_income, user_context):
        """Create personalized system prompt"""
        prompt = """You are MoneyMentor, an expert Indian financial advisor. Provide practical, actionable advice.

**Your Expertise:**
- Indian tax laws (80C, 80D, HRA, etc.)
- Indian investment options (ELSS, PPF, NPS, Mutual Funds)
- Indian banking and financial products
- Rupee-based calculations and scenarios

**Guidelines:**
- Keep responses concise (under 300 words)
- Use bullet points and emojis for clarity
- Focus on actionable steps
- Mention specific Indian financial products
- Always consider tax implications
"""
        
        # Add user context if available
        if user_income:
            income_range = self.get_income_bracket(user_income)
            prompt += f"\n**User Profile:** Monthly income in {income_range} range"
        
        if user_context:
            prompt += f"\n**Context:** {user_context}"
        
        prompt += "\n\nProvide helpful, specific advice for Indian investors."
        
        return prompt
    
    def call_openrouter_api(self, system_prompt, user_message):
        """Call OpenRouter API with error handling"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://moneymentor.app",  # Optional
                "X-Title": "MoneyMentor AI"  # Optional
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 400,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content'].strip()
            
            # Log error for debugging
            print(f"OpenRouter API Error: {response.status_code} - {response.text}")
            return None
            
        except requests.exceptions.Timeout:
            print("OpenRouter API timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("OpenRouter API connection error")
            return None
        except Exception as e:
            print(f"OpenRouter API unexpected error: {str(e)}")
            return None
    
    def get_fallback_response(self, user_message):
        """Get fallback response based on keywords"""
        message_lower = user_message.lower()
        
        # Check each category for keyword matches
        for category, data in self.fallback_responses.items():
            if any(keyword in message_lower for keyword in data['keywords']):
                return data['response']
        
        # Default fallback response
        return """I'm here to help with your financial questions! I can assist with:

🔹 **Tax Planning:** 80C, 80D deductions, tax-saving investments
🔹 **Investment Advice:** SIP, mutual funds, portfolio allocation  
🔹 **Budget Planning:** 50/30/20 rule, expense management
🔹 **Goal Planning:** House, car, retirement planning

Please ask me something specific about any of these topics!"""
    
    def get_income_bracket(self, monthly_income):
        """Get income bracket for context"""
        if monthly_income < 30000:
            return "₹10K-30K"
        elif monthly_income < 50000:
            return "₹30K-50K"
        elif monthly_income < 100000:
            return "₹50K-1L"
        elif monthly_income < 200000:
            return "₹1L-2L"
        else:
            return "₹2L+"
    
    def get_contextual_response(self, query_type, user_income, specific_question):
        """Get contextual response based on query type"""
        context_prompts = {
            'investment': f"User earns ₹{user_income:,.0f}/month and asks about investments: {specific_question}",
            'tax': f"User earns ₹{user_income:,.0f}/month and asks about tax planning: {specific_question}",
            'budget': f"User earns ₹{user_income:,.0f}/month and asks about budgeting: {specific_question}",
            'goal': f"User earns ₹{user_income:,.0f}/month and asks about financial goals: {specific_question}"
        }
        
        if query_type in context_prompts:
            return self.get_response(context_prompts[query_type], user_income)
        else:
            return self.get_response(specific_question, user_income)
    
    def validate_api_key(self):
        """Validate if OpenRouter API key is working"""
        if not self.api_key or self.api_key == 'your-openrouter-api-key':
            return False, "API key not configured"
        
        try:
            test_response = self.call_openrouter_api(
                "You are a helpful assistant.", 
                "Say 'API working' if you can respond."
            )
            
            if test_response:
                return True, "API key is working"
            else:
                return False, "API key validation failed"
                
        except Exception as e:
            return False, f"API validation error: {str(e)}"
    
    def get_ai_insights(self, financial_data):
        """Get AI insights based on user's financial data"""
        if not financial_data:
            return "No financial data available for insights."
        
        insights_prompt = f"""Analyze this financial data and provide 3 key insights:

Income: ₹{financial_data.get('income', 0):,.0f}/month
Savings Rate: {financial_data.get('savings_rate', 0)}%
Risk Appetite: {financial_data.get('risk_appetite', 'moderate')}
Investment Amount: ₹{financial_data.get('investment_amount', 0):,.0f}/month

Give specific, actionable insights for improvement."""
        
        response = self.get_response(insights_prompt, financial_data.get('income'))
        return response
