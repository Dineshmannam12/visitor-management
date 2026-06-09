# Shared configuration for all services
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '6!Admin@123',
    'database': 'visitor_management',
    'autocommit': True,
    'buffered': True
}

# Service Ports
API_GATEWAY_PORT = 8080
SECURITY_SERVICE_PORT = 8081
ADMIN_SERVICE_PORT = 8082
VISITOR_SERVICE_PORT = 8083
REPORT_SERVICE_PORT = 8084

# Company Branding
COMPANY_NAME = "Pi Datacenters"
COMPANY_TAGLINE = "Secure Facility Access Management"

# Logo Configuration
LOGO_PATH = 'static/logo.png'  # Place your logo.png in static folder

# Email Configuration (Update with your email credentials)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'mannamdinesh143@gmail.com',  # Update this
    'sender_password': 'vkci wxiu meul oqbd',   # Update this
    'use_tls': True
}

def get_logo_base64():
    """Convert logo to base64 for embedding in HTML"""
    if os.path.exists(LOGO_PATH):
        import base64
        with open(LOGO_PATH, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode('utf-8')
            ext = LOGO_PATH.split('.')[-1].lower()
            mime_type = 'image/png' if ext == 'png' else 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f'data:{mime_type};base64,{logo_data}'
    return None
