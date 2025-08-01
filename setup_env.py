import os
import secrets
import string
from cryptography.fernet import Fernet

def generate_secret_key(length=32):
    """Generate a cryptographically secure secret key"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) 
                   for _ in range(length))

def generate_encryption_key():
    """Generate encryption key for Fernet"""
    return Fernet.generate_key().decode()

def setup_environment():
    """Automated environment setup"""
    print("🔧 Setting up MoneyMentor Environment...")
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return
    
    # Generate secure keys
    secret_key = generate_secret_key(64)
    encryption_key = generate_encryption_key()
    
    # Get user inputs
    print("\n📝 Please provide the following information:")
    
    openrouter_key = input("OpenRouter API Key (press Enter to skip): ").strip()
    if not openrouter_key:
        openrouter_key = "your-openrouter-api-key"
    
    email = input("SMTP Email (press Enter to skip): ").strip()
    if not email:
        email = "your-email@gmail.com"
    
    email_password = input("SMTP Password (press Enter to skip): ").strip()
    if not email_password:
        email_password = "your-app-password"
    
    domain = input("Your domain (press Enter for localhost): ").strip()
    if not domain:
        domain = "localhost"
    
    # Create .env file
    env_content = f"""# MoneyMentor Environment Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY={secret_key}
DATABASE_URL=sqlite:///database.db

# Security Settings
ENCRYPTION_KEY={encryption_key}
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_PER_MINUTE=60

# OpenRouter AI Settings
OPENROUTER_API_KEY={openrouter_key}
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={email}
SMTP_PASSWORD={email_password}

# Privacy Settings
DATA_RETENTION_DAYS=365
ANONYMIZE_LOGS=True
GDPR_COMPLIANCE=True

# Deployment Settings
ALLOWED_HOSTS={domain},127.0.0.1,localhost
CORS_ORIGINS=http://localhost:5000,https://{domain}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment file created successfully!")
    print("🔐 Secure keys generated automatically")
    print("📝 Please update API keys in .env file before running the application")
    
    # Create .gitignore if it doesn't exist
    if not os.path.exists('.gitignore'):
        gitignore_content = """# Environment variables
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
"""
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("📄 .gitignore file created")

if __name__ == "__main__":
    from datetime import datetime
    setup_environment()
