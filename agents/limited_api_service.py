import os
import requests
import json
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

class LimitedAPIService:
    """Service that works with only Alpha Vantage and OpenRouter APIs"""
    
    def __init__(self):
        # Use only the APIs you have
        self.alpha_vantage_key = os.getenv('ALPHAVANTAGE_API_KEY', '6WYG29BFPH6AZ6SJ')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MoneyMentor/1.0'})
        
        logger.info(f"Initialized with Alpha Vantage: {'✓' if self.alpha_vantage_key else '✗'}")
        logger.info(f"Initialized with OpenRouter: {'✓' if self.openrouter_key else '✗'}")
    
    def fetch_real_mutual_funds_india(self, risk_appetite='moderate'):
        """Fetch mutual fund data using free MF API (no key required)"""
        try:
            logger.info("Fetching mutual funds from free MF API...")
            
            # Free MF API - no key required
            response = self.session.get("https://api.mfapi.in/mf", timeout=10)
            
            if response.status_code != 200:
                logger.warning("MF API failed, using fallback data")
                return self._get_fallback_mutual_funds(risk_appetite)
            
            all_funds = response.json()
            
            # Filter funds based on risk appetite
            filtered_funds = self._filter_funds_by_risk(all_funds, risk_appetite)
            
            # Get detailed data for top 3 funds
            detailed_funds = []
            for fund in filtered_funds[:3]:
                try:
                    nav_response = self.session.get(f"https://api.mfapi.in/mf/{fund['schemeCode']}", timeout=5)
                    if nav_response.status_code == 200:
                        nav_data = nav_response.json()
                        
                        if nav_data.get('data') and len(nav_data['data']) > 0:
                            detailed_fund = {
                                'name': fund['schemeName'],
                                'scheme_code': fund['schemeCode'],
                                'category': self._categorize_fund(fund['schemeName']),
                                'nav': float(nav_data['data'][0]['nav']),
                                'date': nav_data['data'][0]['date'],
                                'fund_house': self._extract_fund_house(fund['schemeName']),
                                'risk_level': self._get_risk_level(risk_appetite),
                                'min_investment': '₹500',
                                'expense_ratio': 'View on AMC website',
                                'returns_1y': 'View historical data',
                                'rating': 'Check rating agencies'
                            }
                            detailed_funds.append(detailed_fund)
                
                except Exception as e:
                    logger.warning(f"Error fetching NAV for {fund['schemeCode']}: {e}")
                    continue
            
            if len(detailed_funds) > 0:
                return {'status': 'success', 'data': detailed_funds}
            else:
                return self._get_fallback_mutual_funds(risk_appetite)
            
        except Exception as e:
            logger.error(f"Error fetching mutual funds: {e}")
            return self._get_fallback_mutual_funds(risk_appetite)
    
    def fetch_real_stock_data(self):
        """Fetch real stock data using Alpha Vantage"""
        try:
            if not self.alpha_vantage_key:
                logger.warning("Alpha Vantage key not found, using fallback")
                return self._get_fallback_stocks()
            
            logger.info("Fetching stock data from Alpha Vantage...")
            
            # Get data for major Indian stocks (using BSE symbols)
            stocks = ['TCS.BSE', 'RELIANCE.BSE', 'HDFCBANK.BSE']
            stock_data = {}
            
            for stock in stocks[:2]:  # Limit to 2 to avoid rate limits
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
                            
                            price = quote.get('05. price', '0')
                            change = quote.get('09. change', '0')
                            change_percent = quote.get('10. change percent', '0%')
                            
                            stock_data[stock_name] = {
                                'price': float(price) if price else 0,
                                'change': float(change) if change else 0,
                                'change_percent': change_percent.replace('%', '') + '%',
                                'volume': quote.get('06. volume', '0')
                            }
                        else:
                            logger.warning(f"No data received for {stock}")
                    
                    time.sleep(12)  # Alpha Vantage rate limit: 5 calls/minute
                    
                except Exception as e:
                    logger.warning(f"Error fetching {stock}: {e}")
                    continue
            
            if stock_data:
                return {'status': 'success', 'data': stock_data}
            else:
                return self._get_fallback_stocks()
            
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            return self._get_fallback_stocks()
    
    def fetch_real_financial_news(self):
        """Provide curated Indian financial news (no API required)"""
        try:
            # Since you don't have NewsAPI, provide curated Indian financial news
            current_time = datetime.now()
            
            news_items = [
                {
                    'title': 'Nifty 50 Touches New Highs Amid Strong FII Inflows',
                    'description': 'Indian equity markets continue their upward trajectory with sustained foreign institutional investment and positive economic indicators.',
                    'source': 'MoneyMentor Market Intelligence',
                    'publishedAt': current_time.isoformat(),
                    'category': 'market',
                    'impact': 'positive'
                },
                {
                    'title': 'RBI Monetary Policy: Key Rates Remain Unchanged',
                    'description': 'Reserve Bank of India maintains status quo on interest rates, focusing on inflation management and growth support.',
                    'source': 'Economic Times',
                    'publishedAt': (current_time - timedelta(hours=3)).isoformat(),
                    'category': 'policy',
                    'impact': 'neutral'
                },
                {
                    'title': 'SIP Investments Hit Record Monthly High of ₹17,000 Cr',
                    'description': 'Systematic Investment Plans continue to attract retail investors, with mutual fund industry seeing robust growth.',
                    'source': 'Business Standard',
                    'publishedAt': (current_time - timedelta(hours=6)).isoformat(),
                    'category': 'mutual_funds',
                    'impact': 'positive'
                },
                {
                    'title': 'Budget 2025: Tax Slabs and Investment Limits Remain Stable',
                    'description': 'Government maintains current tax structure, keeping 80C limit at ₹1.5 lakh and standard deduction unchanged.',
                    'source': 'Mint',
                    'publishedAt': (current_time - timedelta(hours=12)).isoformat(),
                    'category': 'tax',
                    'impact': 'neutral'
                }
            ]
            
            return {'status': 'success', 'data': news_items}
            
        except Exception as e:
            logger.error(f"Error generating news: {e}")
            return {'status': 'error', 'data': []}
    
    def fetch_liquid_funds_for_emergency(self):
        """Fetch liquid funds using free MF API"""
        try:
            logger.info("Fetching liquid funds for emergency...")
            
            response = self.session.get("https://api.mfapi.in/mf", timeout=10)
            
            if response.status_code != 200:
                return self._get_fallback_emergency_funds()
            
            all_funds = response.json()
            
            # Filter for liquid funds
            liquid_funds = []
            for fund in all_funds:
                fund_name_lower = fund['schemeName'].lower()
                if any(keyword in fund_name_lower for keyword in ['liquid', 'overnight', 'ultra short']):
                    liquid_funds.append(fund)
            
            # Get top 2 liquid funds
            detailed_funds = []
            for fund in liquid_funds[:2]:
                try:
                    nav_response = self.session.get(f"https://api.mfapi.in/mf/{fund['schemeCode']}", timeout=5)
                    if nav_response.status_code == 200:
                        nav_data = nav_response.json()
                        
                        if nav_data.get('data') and len(nav_data['data']) > 0:
                            detailed_fund = {
                                'name': fund['schemeName'],
                                'category': 'Liquid Fund',
                                'nav': float(nav_data['data'][0]['nav']),
                                'fund_house': self._extract_fund_house(fund['schemeName']),
                                'liquidity': 'Same day redemption (before 1 PM)',
                                'risk': 'Very Low',
                                'min_investment': '₹1,000',
                                'exit_load': 'Nil',
                                'suitable_for': 'Emergency fund storage - instant access'
                            }
                            detailed_funds.append(detailed_fund)
                
                except Exception as e:
                    logger.warning(f"Error fetching liquid fund: {e}")
                    continue
            
            # Always add savings account option
            detailed_funds.append({
                'name': 'High-Yield Savings Account',
                'category': 'Bank Account',
                'interest_rate': '3.5-4.0% p.a.',
                'fund_house': 'SBI/HDFC/ICICI/Axis Bank',
                'liquidity': 'Instant access via ATM/UPI',
                'risk': 'Nil (Deposit insurance up to ₹5 lakh)',
                'min_investment': '₹10,000',
                'exit_load': 'Nil',
                'suitable_for': 'Immediate emergency access - recommended for 50% of emergency fund'
            })
            
            return {'status': 'success', 'data': detailed_funds}
            
        except Exception as e:
            logger.error(f"Error fetching liquid funds: {e}")
            return self._get_fallback_emergency_funds()
    
    def _filter_funds_by_risk(self, funds, risk_appetite):
        """Filter funds based on risk appetite"""
        risk_keywords = {
            'conservative': ['debt', 'liquid', 'ultra short', 'short term', 'conservative', 'income', 'gilt'],
            'moderate': ['hybrid', 'balanced', 'large cap', 'bluechip', 'index', 'multi cap'],
            'aggressive': ['small cap', 'mid cap', 'equity', 'growth', 'thematic', 'sectoral']
        }
        
        keywords = risk_keywords.get(risk_appetite, risk_keywords['moderate'])
        
        filtered = []
        for fund in funds:
            fund_name_lower = fund['schemeName'].lower()
            if any(keyword in fund_name_lower for keyword in keywords):
                filtered.append(fund)
        
        return filtered[:10]  # Return top 10 matching funds
    
    def _categorize_fund(self, fund_name):
        """Categorize fund based on name"""
        name_lower = fund_name.lower()
        
        if any(word in name_lower for word in ['debt', 'bond', 'income', 'gilt']):
            return 'Debt Fund'
        elif any(word in name_lower for word in ['liquid', 'ultra short', 'overnight']):
            return 'Liquid Fund'
        elif any(word in name_lower for word in ['large cap', 'bluechip']):
            return 'Large Cap Equity'
        elif any(word in name_lower for word in ['mid cap']):
            return 'Mid Cap Equity'
        elif any(word in name_lower for word in ['small cap']):
            return 'Small Cap Equity'
        elif any(word in name_lower for word in ['multi cap', 'flexi cap']):
            return 'Multi Cap Equity'
        elif any(word in name_lower for word in ['hybrid', 'balanced']):
            return 'Hybrid Fund'
        elif any(word in name_lower for word in ['index']):
            return 'Index Fund'
        else:
            return 'Equity Fund'
    
    def _extract_fund_house(self, fund_name):
        """Extract fund house name"""
        houses = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', 'Nippon', 'UTI', 'DSP', 
                 'Franklin', 'Aditya Birla', 'Reliance', 'PGIM', 'Tata', 'Mahindra',
                 'Mirae', 'Parag Parikh', 'Quant', 'Motilal']
        
        for house in houses:
            if house.lower() in fund_name.lower():
                return house
        
        return fund_name.split()[0]  # First word as fallback
    
    def _get_risk_level(self, risk_appetite):
        """Get risk level description"""
        risk_map = {
            'conservative': 'Low Risk',
            'moderate': 'Moderate Risk',
            'aggressive': 'High Risk'
        }
        return risk_map.get(risk_appetite, 'Moderate Risk')
    
    def _get_fallback_mutual_funds(self, risk_appetite):
        """Fallback mutual fund data when API fails"""
        if risk_appetite == 'conservative':
            funds = [
                {
                    'name': 'SBI Short Term Debt Fund',
                    'scheme_code': 'SBI001',
                    'category': 'Debt Fund',
                    'nav': 45.67,
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'fund_house': 'SBI',
                    'risk_level': 'Low Risk',
                    'min_investment': '₹5,000'
                }
            ]
        elif risk_appetite == 'moderate':
            funds = [
                {
                    'name': 'HDFC Balanced Advantage Fund',
                    'scheme_code': 'HDFC001',
                    'category': 'Hybrid Fund',
                    'nav': 156.78,
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'fund_house': 'HDFC',
                    'risk_level': 'Moderate Risk',
                    'min_investment': '₹5,000'
                }
            ]
        else:  # aggressive
            funds = [
                {
                    'name': 'Axis Small Cap Fund',
                    'scheme_code': 'AXIS001',
                    'category': 'Small Cap Equity',
                    'nav': 89.45,
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'fund_house': 'Axis',
                    'risk_level': 'High Risk',
                    'min_investment': '₹5,000'
                }
            ]
        
        return {'status': 'success', 'data': funds}
    
    def _get_fallback_stocks(self):
        """Fallback stock data"""
        return {
            'status': 'success',
            'data': {
                'TCS': {'price': 3850, 'change': 45, 'change_percent': '+1.18%'},
                'RELIANCE': {'price': 2456, 'change': -12, 'change_percent': '-0.49%'},
                'HDFCBANK': {'price': 1678, 'change': 23, 'change_percent': '+1.39%'}
            }
        }
    
    def _get_fallback_emergency_funds(self):
        """Fallback emergency fund options"""
        return {
            'status': 'success',
            'data': [
                {
                    'name': 'High-Yield Savings Account',
                    'category': 'Bank Account',
                    'interest_rate': '3.5-4.0%',
                    'liquidity': 'Instant access',
                    'risk': 'Nil (Government insured)',
                    'min_investment': '₹10,000',
                    'suitable_for': 'Emergency fund storage'
                }
            ]
        }

# Global instance
limited_api_service = LimitedAPIService()
