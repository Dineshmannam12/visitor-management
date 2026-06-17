from flask import Flask, render_template_string, redirect, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import base64
import os
from db_utils import get_db

app = Flask(__name__)
app.secret_key = 'gateway_secret_key_2024'
CORS(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'logo.png', mimetype='image/png')

LOGO_PATH = 'static/logo.png'
BACKGROUND_PATH = 'static/background.jpg'  # Add your background image here

def get_logo_base64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode('utf-8')
            ext = LOGO_PATH.split('.')[-1].lower()
            mime_type = 'image/png' if ext == 'png' else 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f'data:{mime_type};base64,{logo_data}'
    return None

def get_background_base64():
    if os.path.exists(BACKGROUND_PATH):
        with open(BACKGROUND_PATH, 'rb') as f:
            bg_data = base64.b64encode(f.read()).decode('utf-8')
            ext = BACKGROUND_PATH.split('.')[-1].lower()
            mime_type = 'image/png' if ext == 'png' else 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            return f'data:{mime_type};base64,{bg_data}'
    return None

def get_user_role(username):
    user_roles = {
        'security': 'security',
        'admin': 'admin',
        'reception': 'reception'
    }
    return user_roles.get(username.lower(), None)

# Service URLs (internal)
SERVICES = {
    'security': 'http://127.0.0.1:8081',
    'admin': 'http://127.0.0.1:8082',
    'visitor': 'http://127.0.0.1:8083',
    'report': 'http://127.0.0.1:8084'
}

GATEWAY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Datacenters - Visitor Management System</title>
    <link rel="icon" type="image/png" href="/favicon.ico">
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
        .header {
            position: relative;
            z-index: 1;
            color: white;
            padding: 40px 20px 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 42px;
            margin-bottom: 5px;
            text-shadow: 0 2px 20px rgba(0,0,0,0.5);
            letter-spacing: 2px;
            font-weight: 700;
        }
        .header p {
            font-size: 18px;
            opacity: 0.9;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
            letter-spacing: 1px;
        }
        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 20px 40px;
        }
        .login-container {
            max-width: 420px;
            margin: 0 auto 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 35px 30px;
            margin-bottom: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .logo-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .logo-img {
            width: 80px;
            height: 80px;
            object-fit: contain;
            margin-bottom: 10px;
            filter: drop-shadow(0 2px 10px rgba(0,0,0,0.1));
        }
        .login-title {
            color: #1e3c72;
            font-size: 26px;
            margin-bottom: 8px;
            text-align: center;
            font-weight: 700;
        }
        .login-subtitle {
            color: #666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 25px;
        }
        input {
            width: 100%;
            padding: 14px 16px;
            margin: 10px 0;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 14px;
            background: rgba(255,255,255,0.9);
            transition: all 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 0 4px rgba(30, 60, 114, 0.1);
            background: white;
        }
        input::placeholder {
            color: #999;
        }
        button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 14px 24px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            margin-top: 10px;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
        }
        .alert {
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 15px;
            display: none;
            font-size: 14px;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            display: block;
            border-left: 4px solid #dc3545;
        }
        .quick-links {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        .quick-link-btn {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            text-align: center;
            padding: 14px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            display: block;
            transition: all 0.3s ease;
            font-size: 15px;
            letter-spacing: 0.5px;
        }
        .quick-link-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
        }
        .quick-link-btn.visitor {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        }
        .footer {
            position: relative;
            z-index: 1;
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-size: 13px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .footer a {
            color: rgba(255,255,255,0.9);
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Pi Datacenters</h1>
        <p>Visitor Management System</p>
    </div>

    <div class="container">
        <div class="login-container">
            <div class="card">
                <div class="logo-container">
                    {% if logo_base64 %}
                        <img src="{{ logo_base64 }}" alt="PI Data Centers Logo" class="logo-img">
                    {% endif %}
                    <h2 class="login-title">Welcome to Pi Datacenters</h2>
                    <p class="login-subtitle">Enter your username to access your portal</p>
                </div>

                <div id="alert" class="alert"></div>

                <input type="text" id="username" placeholder="Enter your username" autocomplete="off">
                <button onclick="doLogin()">Sign In</button>

                <div class="quick-links">
                    <a href="/visitor/" class="quick-link-btn visitor">📝 Pre-Visitor Registration</a>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        &copy; 2026 Pi Datacenters. All rights reserved.
    </div>

    <script>
        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const alertDiv = document.getElementById('alert');

            if (!username) {
                alertDiv.textContent = 'Please enter your username';
                alertDiv.className = 'alert alert-error';
                return;
            }

            alertDiv.style.display = 'none';

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });

                const result = await response.json();

                if (result.success) {
                    if (result.role === 'admin') {
                        window.location.href = '/admin/';
                    } else if (result.role === 'security') {
                        window.location.href = '/security/';
                    } else if (result.role === 'reception') {
                        window.location.href = '/security/';
                    }
                } else {
                    alertDiv.textContent = result.message || 'Invalid username';
                    alertDiv.className = 'alert alert-error';
                }
            } catch (error) {
                alertDiv.textContent = 'Login failed. Please try again.';
                alertDiv.className = 'alert alert-error';
            }
        }

        document.getElementById('username').addEventListener('keypress', function(e) {
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
    return render_template_string(GATEWAY_TEMPLATE, logo_base64=logo_base64, background_base64=background_base64)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'success': False, 'message': 'Username required'})

    role = get_user_role(username)

    if role:
        return jsonify({'success': True, 'username': username, 'role': role})
    else:
        return jsonify({'success': False, 'message': 'Invalid username. Valid usernames: admin, security, reception'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'gateway', 'timestamp': datetime.now().isoformat()})

# Proxy routes for services
@app.route('/security/')
@app.route('/security/<path:path>')
def security_portal(path=''):
    if path:
        return redirect(f'{SERVICES["security"]}/{path}')
    return redirect(SERVICES['security'])

@app.route('/admin/')
@app.route('/admin/<path:path>')
def admin_portal(path=''):
    if path:
        return redirect(f'{SERVICES["admin"]}/{path}')
    return redirect(SERVICES['admin'])

@app.route('/visitor/')
@app.route('/visitor/<path:path>')
def visitor_portal(path=''):
    if path:
        return redirect(f'{SERVICES["visitor"]}/{path}')
    return redirect(SERVICES['visitor'])

@app.route('/report/')
@app.route('/report/<path:path>')
def report_portal(path=''):
    if path:
        return redirect(f'{SERVICES["report"]}/{path}')
    return redirect(SERVICES['report'])

def redirect(url):
    from flask import redirect as flask_redirect
    return flask_redirect(url)

if __name__ == '__main__':
    print("=" * 60)
    print("🚪 API Gateway running on port 8080")
    print("   URL: http://127.0.0.1:8080")
    print("=" * 60)
    app.run(host='127.0.0.1', port=8080, debug=False)
