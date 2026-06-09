from flask import Flask, request, jsonify, render_template_string, redirect
from flask_cors import CORS
from datetime import datetime
from config import PI_LOGO_SVG

app = Flask(__name__)
CORS(app)

GATEWAY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Data Centers - Visitor Management System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 36px;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .service-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .service-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .service-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .service-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
        }
        .service-icon img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        .service-card h3 {
            color: #1e3c72;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .service-card p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.5;
            font-size: 14px;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        .security-badge { background: #2196F3; color: white; }
        .admin-badge { background: #f44336; color: white; }
        .visitor-badge { background: #4caf50; color: white; }
        .report-badge { background: #ff9800; color: white; }
        .status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 10px;
            font-size: 12px;
            z-index: 1000;
        }
        .service-status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .online { background: #4caf50; }
        .offline { background: #f44336; }
        .login-demo {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin-top: 40px;
            text-align: center;
        }
        .login-demo p {
            color: white;
            font-size: 14px;
        }
        .login-demo code {
            background: rgba(0,0,0,0.3);
            padding: 5px 10px;
            border-radius: 5px;
            margin: 0 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏢 Pi Data Centers</h1>
        <p>Visitor Management System - Microservices Architecture</p>
    </div>
    
    <div class="container">
        <div class="service-grid">
            <div class="service-card" onclick="openService('security')">
                <div class="service-icon">
                    <img src="{{ logo }}" alt="PI Logo">
                </div>
                <h3>Pi Security Login</h3>
                <p>Check-in / Check-out visitors<br>View approved appointments<br>Cannot modify approvals</p>
                <span class="badge security-badge">Port 8081</span>
                <div style="margin-top: 10px;">
                    <span class="service-status" id="security-status"></span>
                    <span id="security-status-text">Checking...</span>
                </div>
            </div>
            
            <div class="service-card" onclick="openService('admin')">
                <div class="service-icon">
                    <img src="{{ logo }}" alt="PI Logo">
                </div>
                <h3>Pi Admin Login</h3>
                <p>Approve/Reject appointments<br>Full system management<br>Email notifications</p>
                <span class="badge admin-badge">Port 8082</span>
                <div style="margin-top: 10px;">
                    <span class="service-status" id="admin-status"></span>
                    <span id="admin-status-text">Checking...</span>
                </div>
            </div>
            
            <div class="service-card" onclick="openService('visitor')">
                <div class="service-icon">
                    <img src="{{ logo }}" alt="PI Logo">
                </div>
                <h3>Visitor Pre-Registration</h3>
                <p>Pre-register your visit<br>Check appointment status<br>Self-service portal</p>
                <span class="badge visitor-badge">Port 8083</span>
                <div style="margin-top: 10px;">
                    <span class="service-status" id="visitor-status"></span>
                    <span id="visitor-status-text">Checking...</span>
                </div>
            </div>
            
            <div class="service-card" onclick="openService('report')">
                <div class="service-icon">
                    <img src="{{ logo }}" alt="PI Logo">
                </div>
                <h3>Reports Portal Login</h3>
                <p>View reports and analytics<br>Export data<br>Email reports</p>
                <span class="badge report-badge">Port 8084</span>
                <div style="margin-top: 10px;">
                    <span class="service-status" id="report-status"></span>
                    <span id="report-status-text">Checking...</span>
                </div>
            </div>
        </div>
        
        <div class="login-demo">
            <p>🔐 Demo Credentials:</p>
            <p>Security: <code>security / security123</code> | Admin: <code>admin / admin123</code> | Reports: <code>reporter / reporter123</code></p>
        </div>
    </div>
    
    <div class="status">
        <strong>System Status</strong><br>
        <span id="system-status">Loading...</span>
    </div>

    <script>
        async function checkService(service, port) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 3000);
                const response = await fetch(`http://localhost:${port}/api/health`, { signal: controller.signal });
                clearTimeout(timeoutId);
                return response.ok;
            } catch(e) {
                return false;
            }
        }
        
        async function updateServiceStatus() {
            const services = [
                {name: 'security', port: 8081},
                {name: 'admin', port: 8082},
                {name: 'visitor', port: 8083},
                {name: 'report', port: 8084}
            ];
            
            let allOnline = true;
            
            for (const service of services) {
                const isOnline = await checkService(service.name, service.port);
                const statusSpan = document.getElementById(`${service.name}-status`);
                const textSpan = document.getElementById(`${service.name}-status-text`);
                
                if (isOnline) {
                    statusSpan.className = 'service-status online';
                    textSpan.textContent = 'Online';
                } else {
                    statusSpan.className = 'service-status offline';
                    textSpan.textContent = 'Offline';
                    allOnline = false;
                }
            }
            
            const systemStatus = document.getElementById('system-status');
            if (allOnline) {
                systemStatus.innerHTML = '✅ All services running';
                systemStatus.style.color = '#4caf50';
            } else {
                systemStatus.innerHTML = '⚠️ Some services are offline';
                systemStatus.style.color = '#ff9800';
            }
        }
        
        function openService(service) {
            window.open(`http://localhost:${service === 'security' ? 8081 : service === 'admin' ? 8082 : service === 'visitor' ? 8083 : 8084}`, '_blank');
        }
        
        updateServiceStatus();
        setInterval(updateServiceStatus, 10000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(GATEWAY_TEMPLATE, logo=PI_LOGO_SVG)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'gateway', 'timestamp': datetime.now().isoformat()})

@app.route('/security')
def security_portal():
    return redirect('http://localhost:8081')

@app.route('/admin')
def admin_portal():
    return redirect('http://localhost:8082')

@app.route('/visitor')
def visitor_portal():
    return redirect('http://localhost:8083')

@app.route('/report')
def report_portal():
    return redirect('http://localhost:8084')

def redirect(url):
    from flask import redirect as flask_redirect
    return flask_redirect(url)

if __name__ == '__main__':
    from db_utils import init_db
    init_db()
    print("🚪 API Gateway running on port 8080")
    print("   Gateway URL: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
