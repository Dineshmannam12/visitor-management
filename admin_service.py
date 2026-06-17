from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_logo_base64, COMPANY_NAME, EMAIL_CONFIG
import json
import traceback
import base64
import os

app = Flask(__name__)
app.secret_key = 'admin_secret_key_2024'
CORS(app)

# Background image path
BACKGROUND_PATH = 'static/background.jpg'

def get_background_base64():
    if os.path.exists(BACKGROUND_PATH):
        with open(BACKGROUND_PATH, 'rb') as f:
            bg_data = base64.b64encode(f.read()).decode('utf-8')
            ext = BACKGROUND_PATH.split('.')[-1].lower()
            mime_type = 'image/png' if ext == 'png' else 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f'data:{mime_type};base64,{bg_data}'
    return None

PURPOSE_MEETING_DETAILS = {
    'Data Center': {
        'Tour': {
            'person_name': 'Mr. Abhinav Kotagiri',
            'email': 'mannamvenkatadinesh@gmail.com'
        },
        'Visit': {
            'person_name': 'Mr. Abhinav Kotagiri',
            'email': 'mannamvenkatadinesh@gmail.com'
        }
    },
    'Maintenance': {
        'IT': {
            'person_name': 'Srikanth',
            'email': 'srikanth@pidatacenters.com'
        },
        'Non IT': {
            'person_name': 'Haneesh',
            'email': 'haneesh@pidatacenters.com'
        }
    },
    'Meeting': {
        'default_email': None
    }
}

# Meeting person mapping with emails
MEETING_PERSON_MAP = {
    'Mr.KVS Prakasa Rao': ('karumudinikhil15@gmail.com', 'Mr.KVS Prakasa Rao'),
    'Mr.Manoj Muppaneni': ('manoj@pidatacenters.com', 'Mr.Manoj Muppaneni'),
    'Mr.Abhinav Kotagiri': ('abhinav.kotagiri@pidatacenters.com', 'Mr.Abhinav Kotagiri'),
    'Mr.Sreekanth Vattipally': ('srikanth@pidatacenters.com', 'Mr.Sreekanth Vattipally'),
    'Mr.Haneesh Kumar': ('haneesh@pidatacenters.com', 'Mr.Haneesh Kumar'),
    'Mr.Kalyan Muppaneni': ('kalyan@pidatacenters.com', 'Mr.Kalyan Muppaneni'),
    'Ms.Swapna Lopelly': ('swapna@pidatacenters.com', 'Ms.Swapna Lopelly')
}

def get_meeting_person_details(meeting_with):
    """Get email and name for meeting person based on the meeting_with value"""
    for name, (email, full_name) in MEETING_PERSON_MAP.items():
        if name.lower() in meeting_with.lower():
            return email, full_name
    return None, None

def send_email(to_email, subject, body):
    if not to_email or to_email == 'string' or '@' not in to_email:
        print(f"⚠️ Invalid email address: {to_email}")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email error to {to_email}: {e}")
        return False

def get_manager_email():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key='manager_email'")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result and result['setting_value'] and result['setting_value'] != 'string' and '@' in result['setting_value']:
                return result['setting_value']
        except Exception as e:
            print(f"Error getting manager email: {e}")
    return None

def get_all_admin_emails():
    emails = []
    manager_email = get_manager_email()
    if manager_email:
        emails.append(manager_email)
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key='additional_emails'")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result and result['setting_value']:
                additional = [e.strip() for e in result['setting_value'].split(',') if e.strip() and '@' in e and e.strip() != 'string']
                emails.extend(additional)
        except Exception as e:
            print(f"Error getting additional emails: {e}")
    valid_emails = []
    for email in list(set(emails)):
        if email and '@' in email and email != 'string':
            valid_emails.append(email)
    return valid_emails

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Admin - PI Data Centers</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            background-image: url('{{ background_base64 }}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            position: relative;
            padding: 20px;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 0;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h2 { color: #1e3c72; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn {
            background: rgba(255,255,255,0.9);
            color: #1e3c72;
            width: auto;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            position: relative;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .tab-btn:hover {
            background: rgba(255,255,255,1);
            transform: translateY(-2px);
        }
        .tab-btn.active {
            background: #1e3c72;
            color: white;
        }
        .tab-count {
            position: absolute;
            top: -8px;
            right: -8px;
            background: #ff4757;
            color: white;
            border-radius: 50%;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
            min-width: 20px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .tab-count.hidden {
            display: none;
        }

        .tab-btn.highlight-pending {
            background: linear-gradient(135deg, #ff9a44, #ff6a00);
            color: white;
            animation: glowPulse 2s infinite;
        }
        .tab-btn.highlight-pending.active {
            background: #1e3c72;
            color: white;
        }
        .tab-btn.highlight-approved {
            background: linear-gradient(135deg, #00b894, #009432);
            color: white;
        }
        .tab-btn.highlight-approved.active {
            background: #1e3c72;
            color: white;
        }
        .tab-btn.highlight-rejected {
            background: linear-gradient(135deg, #ff7675, #d63031);
            color: white;
        }
        .tab-btn.highlight-rejected.active {
            background: #1e3c72;
            color: white;
        }

        @keyframes glowPulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 106, 0, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 106, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 106, 0, 0); }
        }

        .tab-content { display: none; animation: fadeIn 0.3s ease; }
        .tab-content.active { display: block; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .visitor-item {
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid #ff9800;
            transition: all 0.3s ease;
        }
        .visitor-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge.pending { background: linear-gradient(135deg, #ff9a44, #ff6a00); color: white; }
        .badge.approved { background: linear-gradient(135deg, #00b894, #009432); color: white; }
        .badge.rejected { background: linear-gradient(135deg, #ff7675, #d63031); color: white; }
        .badge-group { background: linear-gradient(135deg, #a29bfe, #6c5ce7); color: white; margin-left: 8px; font-size: 10px; padding: 2px 8px; border-radius: 12px; }

        .btn-small {
            width: auto;
            padding: 8px 16px;
            font-size: 13px;
            margin: 5px;
            display: inline-block;
            border-radius: 5px;
            cursor: pointer;
            border: none;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-small:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .btn-approve { background: linear-gradient(135deg, #00b894, #009432); }
        .btn-reject { background: linear-gradient(135deg, #ff7675, #d63031); }
        .btn-undo { background: linear-gradient(135deg, #fdcb6e, #f39c12); }
        .btn-delete { background: linear-gradient(135deg, #ff7675, #d63031); }

        .top-bar {
            background: rgba(0,0,0,0.85);
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-radius: 12px;
            color: white;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .top-bar .brand {
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .top-bar .brand span {
            color: #64b5f6;
        }
        .top-bar-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .top-bar a {
            color: rgba(255,255,255,0.85);
            text-decoration: none;
            padding: 6px 14px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .top-bar a:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }
        .top-bar .user-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: rgba(255,255,255,0.9);
            padding: 6px 12px;
            background: rgba(255,255,255,0.08);
            border-radius: 6px;
        }
        .top-bar .user-info .user-icon {
            font-size: 18px;
        }
        .logout-btn {
            background: #e74c3c !important;
            color: white !important;
            padding: 8px 20px !important;
            border: none !important;
            border-radius: 6px !important;
            cursor: pointer;
            font-size: 14px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: auto !important;
        }
        .logout-btn:hover {
            background: #c0392b !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        }

        input, textarea {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
        }

        .alert { 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 15px; 
            display: none; 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            z-index: 1000; 
            min-width: 300px; 
            animation: slideInRight 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .alert-success { background: #d4edda; color: #155724; display: block; border-left: 4px solid #28a745; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; border-left: 4px solid #dc3545; }
        .alert-info { background: #d1ecf1; color: #0c5460; display: block; border-left: 4px solid #17a2b8; }
        .alert-warning { background: #fff3cd; color: #856404; display: block; border-left: 4px solid #ffc107; }

        .logo-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .logo-img {
            width: 80px;
            height: 80px;
            object-fit: contain;
            margin-bottom: 10px;
        }
        .login-title {
            color: #1e3c72;
            font-size: 24px;
            margin-top: 10px;
        }
        .login-subtitle {
            color: #666;
            font-size: 14px;
        }
        .rejection-reason {
            background: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 12px;
            color: #856404;
            border-left: 3px solid #ffc107;
        }
        .group-members {
            background: #e8eaf6;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 12px;
        }
        .group-members ul {
            margin-left: 20px;
            margin-top: 5px;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        .stat-card h4 {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .stat-card p {
            font-size: 32px;
            font-weight: bold;
            color: #1e3c72;
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            border-radius: 10px;
        }

        /* Login Page Styles with Background Image */
        .login-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 90vh;
            padding: 20px;
        }

        .login-card {
            display: flex;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            max-width: 1000px;
            width: 100%;
            overflow: hidden;
            animation: slideUp 0.6s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .login-left {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 50px 40px;
            width: 45%;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .login-brand h1 {
            font-size: 32px;
            font-weight: 700;
            margin: 10px 0 5px;
        }

        .login-brand p {
            opacity: 0.8;
            font-size: 14px;
        }

        .brand-icon {
            font-size: 50px;
            display: block;
        }

        .login-features {
            margin: 30px 0;
        }

        .feature-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .feature-item:last-child {
            border-bottom: none;
        }

        .feature-icon {
            font-size: 20px;
            width: 30px;
        }

        .login-footer-links {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .login-footer-links a {
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s ease;
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            text-align: center;
        }

        .login-footer-links a:hover {
            background: rgba(255,255,255,0.2);
            color: white;
            transform: translateX(5px);
        }

        .login-right {
            padding: 50px 40px;
            width: 55%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-header h2 {
            color: #1e3c72;
            font-size: 28px;
            margin: 10px 0 5px;
        }

        .login-header p {
            color: #666;
            font-size: 14px;
        }

        .input-group {
            position: relative;
            margin-bottom: 20px;
        }

        .input-icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 18px;
            color: #999;
        }

        .input-group input {
            width: 100%;
            padding: 14px 15px 14px 45px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.9);
        }

        .input-group input:focus {
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
            background: white;
        }

        .login-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
        }

        .btn-arrow {
            transition: transform 0.3s ease;
            display: inline-block;
        }

        .login-btn:hover .btn-arrow {
            transform: translateX(5px);
        }

        .login-divider {
            text-align: center;
            margin: 25px 0 20px;
            position: relative;
        }

        .login-divider::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            width: 100%;
            height: 1px;
            background: #e0e0e0;
        }

        .login-divider span {
            background: rgba(255,255,255,0.95);
            padding: 0 15px;
            color: #999;
            font-size: 12px;
            position: relative;
            z-index: 1;
        }

        .quick-actions {
            display: flex;
            gap: 12px;
        }

        .quick-action-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            text-decoration: none;
            color: #1e3c72;
            text-align: center;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-weight: 500;
            font-size: 14px;
        }

        .quick-action-btn:hover {
            border-color: #1e3c72;
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(30, 60, 114, 0.15);
        }

        .action-icon {
            font-size: 18px;
        }

        @media (max-width: 768px) {
            .login-card {
                flex-direction: column;
                margin: 10px;
            }
            .login-left {
                width: 100%;
                padding: 30px;
            }
            .login-right {
                width: 100%;
                padding: 30px;
            }
            .login-features {
                display: none;
            }
            .login-footer-links {
                flex-direction: row;
                margin-top: 15px;
            }
            .login-footer-links a {
                flex: 1;
                font-size: 12px;
                padding: 6px 10px;
            }
            .top-bar {
                flex-direction: column;
                gap: 10px;
                padding: 12px 15px;
            }
            .top-bar-right {
                flex-wrap: wrap;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div id="loginPage">
        <div class="container">
            <div class="login-wrapper">
                <div class="login-card">
                    <div class="login-left">
                        <div class="login-brand">
                            <h1>Admin Portal</h1>
                            <p>Pi Datacenters Management</p>
                        </div>
                        <div class="login-features">
                            <div class="feature-item">
                                <span class="feature-icon">✅</span>
                                <span>Manage Appointments</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">📊</span>
                                <span>Generate Reports</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">⚙️</span>
                                <span>System Settings</span>
                            </div>
                        </div>
                    </div>
                    <div class="login-right">
                        <div class="login-header">
                            <div class="logo-container">
                                {% if logo_base64 %}
                                    <img src="{{ logo_base64 }}" alt="PI Data Centers" class="logo-img">
                                {% endif %}
                            </div>
                            <h2>Welcome Back</h2>
                            <p>Sign in to your admin account</p>
                        </div>
                        <div id="loginAlert" class="alert" style="display:none;"></div>
                        <form id="loginForm" onsubmit="return false;">
                            <div class="input-group">
                                <div class="input-icon">👤</div>
                                <input type="text" id="username" placeholder="Username" autocomplete="off">
                            </div>
                            <div class="input-group">
                                <div class="input-icon">🔒</div>
                                <input type="password" id="password" placeholder="Password">
                            </div>
                            <button type="button" onclick="doLogin()" class="login-btn">
                                <span>Sign In</span>
                                <span class="btn-arrow">→</span>
                            </button>
                        </form>
                        <div class="login-divider">
                            <span>or continue with</span>
                        </div>
                        <div class="quick-actions">
                            <a href="/report/" class="quick-action-btn">
                                <span class="action-icon">📊</span>
                                <span>Reports</span>
                            </a>
                            <a href="/" class="quick-action-btn">
                                <span class="action-icon">🏠</span>
                                <span>Gateway</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="mainApp" style="display:none;">
        <div class="top-bar">
            <div class="brand">
                👑 Pi Datacenters <span>Admin Portal</span>
            </div>
            <div class="top-bar-right">
                <a href="/report/">📊 Reports</a>
                <div class="user-info">
                    <span class="user-icon">👤</span>
                    <span id="currentUser"></span>
                </div>
                <button class="logout-btn" onclick="doLogout()">🚪 Logout</button>
            </div>
        </div>
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>📊 Total Appointments</h4>
                    <p id="totalCount">0</p>
                </div>
                <div class="stat-card">
                    <h4>⏳ Pending Approval</h4>
                    <p id="statPendingCount">0</p>
                </div>
                <div class="stat-card">
                    <h4>✅ Approved</h4>
                    <p id="statApprovedCount">0</p>
                </div>
                <div class="stat-card">
                    <h4>❌ Rejected</h4>
                    <p id="statRejectedCount">0</p>
                </div>
            </div>

            <div class="tabs">
                <button class="tab-btn active" id="pendingTabBtn" onclick="showTab('pending')">
                    ⏳ Pending Approvals
                    <span id="pendingCount" class="tab-count">0</span>
                </button>
                <button class="tab-btn" id="approvedTabBtn" onclick="showTab('approved')">
                    ✅ Approved
                    <span id="approvedCount" class="tab-count">0</span>
                </button>
                <button class="tab-btn" id="rejectedTabBtn" onclick="showTab('rejected')">
                    ❌ Rejected
                    <span id="rejectedCount" class="tab-count">0</span>
                </button>
                <button class="tab-btn" id="settingsTabBtn" onclick="showTab('settings')">
                    ⚙️ Email Settings
                </button>
            </div>

            <div id="pendingTab" class="tab-content active">
                <div class="card">
                    <h2>⏳ Pending Approval Requests</h2>
                    <div id="pendingList"></div>
                </div>
            </div>

            <div id="approvedTab" class="tab-content">
                <div class="card">
                    <h2>✅ Approved Appointments</h2>
                    <div id="approvedList"></div>
                </div>
            </div>

            <div id="rejectedTab" class="tab-content">
                <div class="card">
                    <h2>❌ Rejected Appointments</h2>
                    <div id="rejectedList"></div>
                </div>
            </div>

            <div id="settingsTab" class="tab-content">
                <div class="card">
                    <h2>⚙️ Email Settings</h2>
                    <label>Manager Email (Primary):</label>
                    <input type="email" id="managerEmail" placeholder="manager@company.com">
                    <label>Additional Emails (comma separated):</label>
                    <textarea id="additionalEmails" rows="3" placeholder="email1@company.com, email2@company.com"></textarea>
                    <button onclick="saveEmailSettings()">Save Email Settings</button>
                    <div id="settingsAlert" class="alert" style="margin-top: 15px;"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="notificationAlert" class="alert" style="display:none;"></div>

    <script>
        let currentUser = null;
        let autoRefreshInterval = null;

        function getBasePath() {
            const pathname = window.location.pathname;
            if (pathname.startsWith('/admin/')) {
                return '/admin';
            }
            return '';
        }

        async function api(url, method='GET', data=null) {
            const basePath = getBasePath();
            let fullUrl = basePath + url;

            const opts = { method, headers: {'Content-Type': 'application/json'}};
            if (data) opts.body = JSON.stringify(data);
            try {
                const res = await fetch(fullUrl, opts);
                const result = await res.json();
                return result;
            } catch(e) {
                console.error('API Error:', e);
                return null;
            }
        }

        function updateCountBadge(elementId, count) {
            const badge = document.getElementById(elementId);
            if (!badge) return;

            if (count > 0) {
                badge.textContent = count;
                badge.classList.remove('hidden');
            } else {
                badge.textContent = '0';
                badge.classList.add('hidden');
            }
        }

        async function updateTabCounts() {
            const pending = await api('/api/appointments?status=pending');
            const approved = await api('/api/appointments?status=approved');
            const rejected = await api('/api/appointments?status=rejected');

            const pendingCount = pending ? pending.length : 0;
            const approvedCount = approved ? approved.length : 0;
            const rejectedCount = rejected ? rejected.length : 0;
            const totalCount = pendingCount + approvedCount + rejectedCount;

            document.getElementById('statPendingCount').textContent = pendingCount;
            document.getElementById('statApprovedCount').textContent = approvedCount;
            document.getElementById('statRejectedCount').textContent = rejectedCount;
            document.getElementById('totalCount').textContent = totalCount;

            updateCountBadge('pendingCount', pendingCount);
            updateCountBadge('approvedCount', approvedCount);
            updateCountBadge('rejectedCount', rejectedCount);

            highlightTab('pendingTabBtn', pendingCount > 0, 'pending');
            highlightTab('approvedTabBtn', approvedCount > 0, 'approved');
            highlightTab('rejectedTabBtn', rejectedCount > 0, 'rejected');

            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab) {
                const activeTabId = activeTab.id;
                if (activeTabId === 'pendingTab') {
                    await loadPendingAppointments();
                } else if (activeTabId === 'approvedTab') {
                    await loadApprovedAppointments();
                } else if (activeTabId === 'rejectedTab') {
                    await loadRejectedAppointments();
                }
            }
        }

        function highlightTab(tabId, hasItems, type) {
            const tabBtn = document.getElementById(tabId);
            if (!tabBtn) return;

            tabBtn.classList.remove('highlight-pending', 'highlight-approved', 'highlight-rejected');

            if (hasItems) {
                if (type === 'pending') {
                    tabBtn.classList.add('highlight-pending');
                } else if (type === 'approved') {
                    tabBtn.classList.add('highlight-approved');
                } else if (type === 'rejected') {
                    tabBtn.classList.add('highlight-rejected');
                }
            }
        }

        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const loginAlert = document.getElementById('loginAlert');

            if (!username || !password) {
                loginAlert.textContent = 'Please enter username and password';
                loginAlert.className = 'alert alert-error';
                loginAlert.style.display = 'block';
                return;
            }

            loginAlert.style.display = 'none';

            const result = await api('/api/login', 'POST', { username, password });
            if (result && result.success && result.role === 'admin') {
                currentUser = result.username;
                sessionStorage.setItem('admin_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadAllData();
                loadEmailSettings();
                updateTabCounts();

                if (autoRefreshInterval) clearInterval(autoRefreshInterval);
                autoRefreshInterval = setInterval(updateTabCounts, 30000);
                showNotification('✅ Welcome back, ' + username + '!', 'success');
            } else {
                loginAlert.textContent = 'Invalid credentials or unauthorized access';
                loginAlert.className = 'alert alert-error';
                loginAlert.style.display = 'block';
            }
        }

        function doLogout() {
            // Clear session
            currentUser = null;
            sessionStorage.removeItem('admin_user');
            
            // Clear auto refresh interval
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
            
            // Show login page, hide main app
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
            
            // Reset form fields
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
            
            // Clear any error messages
            const loginAlert = document.getElementById('loginAlert');
            loginAlert.style.display = 'none';
            loginAlert.className = 'alert';
            
            // Show notification
            showNotification('👋 Logged out successfully', 'info');
        }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

            document.getElementById(tab + 'Tab').classList.add('active');

            const tabButtons = document.querySelectorAll('.tab-btn');
            let tabIndex = { pending: 0, approved: 1, rejected: 2, settings: 3 }[tab];
            if (tabButtons[tabIndex]) {
                tabButtons[tabIndex].classList.add('active');
            }

            if (tab === 'pending') loadPendingAppointments();
            if (tab === 'approved') loadApprovedAppointments();
            if (tab === 'rejected') loadRejectedAppointments();
        }

        async function loadAllData() {
            await loadPendingAppointments();
            await loadApprovedAppointments();
            await loadRejectedAppointments();
        }

        function getEmptyStateMessage(type) {
            const messages = {
                pending: { icon: '📭', text: 'No pending requests to review' },
                approved: { icon: '✅', text: 'No approved appointments yet' },
                rejected: { icon: '❌', text: 'No rejected appointments' }
            };
            const msg = messages[type] || { icon: '📋', text: 'No records found' };
            return `<div class="empty-state">
                        <div class="empty-state-icon">${msg.icon}</div>
                        <div>${msg.text}</div>
                    </div>`;
        }

        function getGroupMembersDisplay(groupMembers, isGroup) {
            if (!isGroup || !groupMembers) return '';
            try {
                const members = JSON.parse(groupMembers);
                if (members && members.length > 0) {
                    let html = '<div class="group-members"><strong>👥 Group Members:</strong><ul>';
                    members.forEach(m => {
                        html += `<li><strong>${escapeHtml(m.name)}</strong> - ${escapeHtml(m.email)}</li>`;
                    });
                    html += '</ul></div>';
                    return html;
                }
            } catch(e) {
                return '';
            }
            return '';
        }

        async function loadPendingAppointments() {
            const apps = await api('/api/appointments?status=pending');
            const container = document.getElementById('pendingList');
            if (!apps || apps.length === 0) {
                container.innerHTML = getEmptyStateMessage('pending');
                return;
            }

            container.innerHTML = apps.map(a => {
                const groupBadge = a.is_group ? '<span class="badge-group">GROUP</span>' : '';
                const groupMembersHtml = getGroupMembersDisplay(a.group_members, a.is_group);
                
                let dataCenterInfo = '';
                if (a.purpose === 'Data Center' && a.data_center_type) {
                    dataCenterInfo = `🏢 Data Center Type: ${escapeHtml(a.data_center_type)}<br>`;
                }

                return `
                    <div class="visitor-item">
                        <strong>${escapeHtml(a.name)}</strong> ${groupBadge}<br>
                        📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                        🏢 ${escapeHtml(a.company_name || 'N/A')}<br>
                        📝 ${escapeHtml(a.purpose)}<br>
                        ${dataCenterInfo}
                        ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                        📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                        ${groupMembersHtml}
                        <span class="badge pending">PENDING</span><br>
                        <button class="btn-small btn-approve" onclick="approveAppt('${a.appointment_id || a.id}')">✅ Approve</button>
                        <button class="btn-small btn-reject" onclick="rejectAppt('${a.appointment_id || a.id}')">❌ Reject</button>
                    </div>
                `;
            }).join('');
        }

        async function loadApprovedAppointments() {
            const apps = await api('/api/appointments?status=approved');
            const container = document.getElementById('approvedList');
            if (!apps || apps.length === 0) {
                container.innerHTML = getEmptyStateMessage('approved');
                return;
            }

            container.innerHTML = apps.map(a => {
                const groupBadge = a.is_group ? '<span class="badge-group">GROUP</span>' : '';
                const groupMembersHtml = getGroupMembersDisplay(a.group_members, a.is_group);
                
                let dataCenterInfo = '';
                if (a.purpose === 'Data Center' && a.data_center_type) {
                    dataCenterInfo = `🏢 Data Center Type: ${escapeHtml(a.data_center_type)}<br>`;
                }

                return `
                    <div class="visitor-item" style="border-left-color:#4caf50;">
                        <strong>${escapeHtml(a.name)}</strong> ${groupBadge}<br>
                        📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                        🏢 ${escapeHtml(a.company_name || 'N/A')}<br>
                        📝 ${escapeHtml(a.purpose)}<br>
                        ${dataCenterInfo}
                        ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                        📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                        ${groupMembersHtml}
                        <span class="badge approved">APPROVED</span><br>
                        <button class="btn-small btn-undo" onclick="undoAppt('${a.appointment_id || a.id}')">↩ Undo</button>
                        <button class="btn-small btn-delete" onclick="deleteAppt('${a.appointment_id || a.id}')">🗑 Delete</button>
                    </div>
                `;
            }).join('');
        }

        async function loadRejectedAppointments() {
            const apps = await api('/api/appointments?status=rejected');
            const container = document.getElementById('rejectedList');
            if (!apps || apps.length === 0) {
                container.innerHTML = getEmptyStateMessage('rejected');
                return;
            }

            container.innerHTML = apps.map(a => {
                const groupBadge = a.is_group ? '<span class="badge-group">GROUP</span>' : '';
                const groupMembersHtml = getGroupMembersDisplay(a.group_members, a.is_group);
                
                let dataCenterInfo = '';
                if (a.purpose === 'Data Center' && a.data_center_type) {
                    dataCenterInfo = `🏢 Data Center Type: ${escapeHtml(a.data_center_type)}<br>`;
                }

                return `
                    <div class="visitor-item" style="border-left-color:#f44336;">
                        <strong>${escapeHtml(a.name)}</strong> ${groupBadge}<br>
                        📧 ${escapeHtml(a.email)}<br>
                        🏢 ${escapeHtml(a.company_name || 'N/A')}<br>
                        📝 ${escapeHtml(a.purpose)}<br>
                        ${dataCenterInfo}
                        ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                        📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                        ${groupMembersHtml}
                        <div class="rejection-reason">
                            ❌ Rejection Reason: ${escapeHtml(a.rejection_reason || 'Not specified')}
                        </div>
                        <span class="badge rejected">REJECTED</span><br>
                        <button class="btn-small btn-undo" onclick="undoAppt('${a.appointment_id || a.id}')">↩ Undo</button>
                        <button class="btn-small btn-delete" onclick="deleteAppt('${a.appointment_id || a.id}')">🗑 Delete</button>
                    </div>
                `;
            }).join('');
        }

        async function approveAppt(id) {
            if (!confirm('Approve this request? The visitor will be notified via email.')) return;
            showNotification('Processing approval...', 'info');

            const result = await api('/api/appointments/' + id + '/status', 'PUT', { status: 'approved' });
            if (result && result.success) {
                const emailResult = await api('/api/email/approval', 'POST', { appointment_id: id });
                if (emailResult && emailResult.success) {
                    showNotification('✅ Approved! Visitor has been notified via email.', 'success');
                } else {
                    showNotification('✅ Approved! But email notification failed. Please check email settings.', 'warning');
                }
                await loadPendingAppointments();
                await loadApprovedAppointments();
                await updateTabCounts();
            } else {
                showNotification('❌ Approval failed. Please try again.', 'error');
            }
        }

        async function rejectAppt(id) {
            const reason = prompt('Please enter the reason for rejection:', 'Your request did not meet our approval criteria.');
            if (reason === null || reason.trim() === '') {
                showNotification('Rejection cancelled - reason is required', 'error');
                return;
            }
            if (!confirm('Reject this request? The visitor and staff will be notified via email.')) return;

            showNotification('Processing rejection...', 'info');

            const result = await api('/api/appointments/' + id + '/status', 'PUT', {
                status: 'rejected',
                rejection_reason: reason
            });

            if (result && result.success) {
                const emailResult = await api('/api/email/rejection', 'POST', {
                    appointment_id: id,
                    reason: reason
                });

                if (emailResult && emailResult.success) {
                    showNotification('❌ Rejected! Visitor and staff have been notified via email.', 'success');
                } else {
                    showNotification('❌ Rejected! But email notification failed. Please check email settings.', 'warning');
                }
                await loadPendingAppointments();
                await loadRejectedAppointments();
                await updateTabCounts();
            } else {
                showNotification('❌ Failed to reject. Please try again.', 'error');
            }
        }

        async function undoAppt(id) {
            if (!confirm('Undo this action? This will set the status back to pending.')) return;
            const result = await api('/api/appointments/' + id + '/status', 'PUT', { status: 'pending' });
            if (result && result.success) {
                showNotification('✅ Status reset to pending!', 'success');
                await loadAllData();
                await updateTabCounts();
            } else {
                showNotification('❌ Failed to undo. Please try again.', 'error');
            }
        }

        async function deleteAppt(id) {
            if (!confirm('Delete this appointment permanently?')) return;
            const result = await api('/api/appointments/' + id, 'DELETE');
            if (result && result.success) {
                showNotification('✅ Appointment deleted!', 'success');
                await loadAllData();
                await updateTabCounts();
            } else {
                showNotification('❌ Failed to delete. Please try again.', 'error');
            }
        }

        async function loadEmailSettings() {
            const manager = await api('/api/settings/manager_email');
            const additional = await api('/api/settings/additional_emails');
            if (manager && manager.value) document.getElementById('managerEmail').value = manager.value;
            if (additional && additional.value) document.getElementById('additionalEmails').value = additional.value;
        }

        async function saveEmailSettings() {
            const managerEmail = document.getElementById('managerEmail').value.trim();
            const additionalEmails = document.getElementById('additionalEmails').value.trim();
            await api('/api/settings/manager_email', 'POST', { value: managerEmail });
            await api('/api/settings/additional_emails', 'POST', { value: additionalEmails });
            showNotification('✅ Email settings saved successfully!', 'success');
        }

        function showNotification(msg, type) {
            const alertDiv = document.getElementById('notificationAlert');
            alertDiv.textContent = msg;
            alertDiv.className = 'alert alert-' + type;
            alertDiv.style.display = 'block';
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 5000);
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Check if user is already logged in
        const savedUser = sessionStorage.getItem('admin_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadAllData();
            loadEmailSettings();
            updateTabCounts();
            autoRefreshInterval = setInterval(updateTabCounts, 30000);
        }

        // Enter key support for login
        document.getElementById('username').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('password').focus();
            }
        });
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                doLogin();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    background_base64 = get_background_base64()
    return render_template_string(ADMIN_TEMPLATE, logo_base64=logo_base64, background_base64=background_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'admin', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return jsonify({'success': True, 'username': user['username'], 'role': user['role']})
        except Exception as e:
            print(f"Login error: {e}")
    return jsonify({'success': False}), 401

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    status = request.args.get('status', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT appointment_id, id, name, email, phone, company_name, vehicle_number, 
                       purpose, meeting_with, appointment_date, notes, status, created_by, 
                       maintenance_type, is_group, group_members, data_center_type, rejection_reason 
                FROM appointments
            """
            params = []
            if status:
                query += " WHERE status=%s"
                params.append(status)
            query += " ORDER BY appointment_date DESC"
            cursor.execute(query, params)
            apps = cursor.fetchall()
            cursor.close()
            conn.close()
            for a in apps:
                if a.get('appointment_date'):
                    a['appointment_date'] = str(a['appointment_date'])
            return jsonify(apps)
        except Exception as e:
            print(f"Error getting appointments: {e}")
            return jsonify([])
    return jsonify([])

@app.route('/api/appointments/<aid>/status', methods=['PUT'])
def update_appointment_status(aid):
    data = request.json
    new_status = data.get('status')
    rejection_reason = data.get('rejection_reason', '')

    print(f"📝 Updating appointment {aid} to status: {new_status}")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()

            if new_status == 'rejected':
                cursor.execute("UPDATE appointments SET status=%s, rejection_reason=%s WHERE appointment_id=%s",
                             (new_status, rejection_reason, aid))
                if cursor.rowcount == 0:
                    cursor.execute("UPDATE appointments SET status=%s, rejection_reason=%s WHERE id=%s",
                                 (new_status, rejection_reason, aid))
            else:
                cursor.execute("UPDATE appointments SET status=%s WHERE appointment_id=%s",
                             (new_status, aid))
                if cursor.rowcount == 0:
                    cursor.execute("UPDATE appointments SET status=%s WHERE id=%s",
                                 (new_status, aid))

            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()

            if affected > 0:
                print(f"✅ Appointment {aid} updated successfully to {new_status}")
                return jsonify({'success': True})
            else:
                print(f"❌ Appointment {aid} not found")
                return jsonify({'success': False, 'error': 'Appointment not found'}), 404
        except Exception as e:
            print(f"❌ Error updating appointment: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

@app.route('/api/appointments/<aid>', methods=['DELETE'])
def delete_appointment(aid):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE appointment_id=%s OR id=%s", (aid, aid))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error deleting appointment: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': True})

@app.route('/api/email/approval', methods=['POST'])
def email_approval():
    data = request.json
    aid = data.get('appointment_id', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE appointment_id=%s OR id=%s", (aid, aid))
            appt = cursor.fetchone()
            cursor.close()
            conn.close()

            if not appt:
                return jsonify({'success': False, 'error': 'Appointment not found'}), 404

            meeting_text = f"\n- Meeting With: {appt.get('meeting_with', 'N/A')}" if appt.get('meeting_with') else ''

            is_group = appt.get('is_group', 0)
            group_members = appt.get('group_members', '')

            if is_group and group_members:
                try:
                    members = json.loads(group_members)
                    visitor_list = ""
                    for idx, m in enumerate(members, 1):
                        visitor_list += f"  {idx}. {m['name']} - {m['email']}\n"

                    body = f"""
Dear Visitor,

Your group visit request to {COMPANY_NAME} has been APPROVED.

📋 Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Contact: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Company: {appt.get('company_name', 'N/A')}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
• Total Visitors: {len(members)}

VISITOR LIST:
{visitor_list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: APPROVED

Please bring valid ID for all visitors.

{COMPANY_NAME} Management
"""
                    send_email(appt['email'], f"✅ Your Group Visit to {COMPANY_NAME} has been APPROVED!", body)

                    for member in members:
                        if member.get('email') and member['email'] != appt['email']:
                            member_body = f"""
Dear {member['name']},

Your visit request to {COMPANY_NAME} as part of a group has been APPROVED.

📋 Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {member['name']}
• Email: {member['email']}
• Company: {appt.get('company_name', 'N/A')}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: APPROVED

Please bring a valid government-issued ID.

{COMPANY_NAME} Management
"""
                            send_email(member['email'], f"✅ Your Visit to {COMPANY_NAME} has been APPROVED!", member_body)
                except Exception as e:
                    print(f"Error sending group approval emails: {e}")
                    body = f"Your visit request to {COMPANY_NAME} has been APPROVED.\n\n📋 Appointment Details:\n• Name: {appt['name']}\n• Email: {appt['email']}\n• Phone: {appt['phone']}\n• Company: {appt.get('company_name', 'N/A')}\n• Purpose: {appt['purpose']}{meeting_text}\n• Date & Time: {appt['appointment_date']}\n\nPlease bring a valid government-issued ID.\n\n{COMPANY_NAME} Management"
                    send_email(appt['email'], f"✅ Your Visit to {COMPANY_NAME} has been APPROVED!", body)
            else:
                body = f"""
Dear {appt['name']},

Your visit request to {COMPANY_NAME} has been APPROVED.

📋 Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Company: {appt.get('company_name', 'N/A')}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: APPROVED

Please bring a valid government-issued ID.

{COMPANY_NAME} Management
"""
                send_email(appt['email'], f"✅ Your Visit to {COMPANY_NAME} has been APPROVED!", body)

            admin_emails = get_all_admin_emails()
            if admin_emails:
                admin_subject = f"✅ Appointment APPROVED - {appt['name']}"
                admin_body = f"APPOINTMENT APPROVED\n\nVisitor: {appt['name']}\nEmail: {appt['email']}\nCompany: {appt.get('company_name', 'N/A')}\nPurpose: {appt['purpose']}{meeting_text}\nDate: {appt['appointment_date']}\n\n{COMPANY_NAME} VMS"
                for email in admin_emails:
                    send_email(email, admin_subject, admin_body)

            return jsonify({'success': True})
        except Exception as e:
            print(f"Approval email error: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': False}), 500

@app.route('/api/email/rejection', methods=['POST'])
def email_rejection():
    data = request.json
    aid = data.get('appointment_id', '')
    reason = data.get('reason', 'Not specified')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE appointment_id=%s OR id=%s", (aid, aid))
            appt = cursor.fetchone()
            cursor.close()
            conn.close()
            if appt:
                meeting_text = f"\n- Meeting With: {appt.get('meeting_with', 'N/A')}" if appt.get('meeting_with') else ''

                is_group = appt.get('is_group', 0)
                group_members = appt.get('group_members', '')

                body = f"""
Dear {appt['name']},

We regret to inform you that your visit request to {COMPANY_NAME} has been REJECTED.

📋 Request Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Company: {appt.get('company_name', 'N/A')}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Rejection Reason:
{reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you believe this is an error or need to reschedule, please contact us.

We appreciate your understanding.

{COMPANY_NAME} Management
"""
                send_email(appt['email'], f"❌ Your Visit to {COMPANY_NAME} has been REJECTED", body)

                if is_group and group_members:
                    try:
                        members = json.loads(group_members)
                        for member in members:
                            if member.get('email') and member['email'] != appt['email']:
                                member_body = f"""
Dear {member['name']},

We regret to inform you that your visit request to {COMPANY_NAME} as part of a group has been REJECTED.

📋 Request Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {member['name']}
• Email: {member['email']}
• Company: {appt.get('company_name', 'N/A')}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Rejection Reason:
{reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you believe this is an error or need to reschedule, please contact us.

We appreciate your understanding.

{COMPANY_NAME} Management
"""
                                send_email(member['email'], f"❌ Your Visit to {COMPANY_NAME} has been REJECTED", member_body)
                    except Exception as e:
                        print(f"Error sending group rejection emails: {e}")
        except Exception as e:
            print(f"Rejection email error: {e}")
            traceback.print_exc()
    return jsonify({'success': True})

@app.route('/api/settings/<key>', methods=['GET'])
def get_setting(key):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key=%s", (key,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                return jsonify({'value': result['setting_value']})
        except Exception as e:
            print(f"Error getting setting: {e}")
    return jsonify({'value': None})

@app.route('/api/settings/<key>', methods=['POST'])
def set_setting(key):
    data = request.json
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET setting_value=%s WHERE setting_key=%s", (data['value'], key))
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s,%s)", (key, data['value']))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error setting setting: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': False}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("👑 Admin Service running on port 8082")
    print("   URL: http://localhost:8082")
    print("   Login: admin / admin123")
    print("=" * 60)
    app.run(host='127.0.0.1', port=8082, debug=False)
