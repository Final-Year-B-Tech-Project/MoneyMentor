from flask import request, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta
import redis
import json

# Simple in-memory rate limiter for development
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier, limit_per_minute):
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit_per_minute:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

# Global rate limiter instance
rate_limiter = SimpleRateLimiter()

def rate_limit(per_minute=None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limit = per_minute or current_app.config.get('RATE_LIMIT_PER_MINUTE', 60)
            
            # Use IP address as identifier
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, limit):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} requests per minute allowed'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
