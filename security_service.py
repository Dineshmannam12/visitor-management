from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import uuid
import base64
import os
from config import get_logo_base64, COMPANY_NAME

app = Flask(__name__)
app.secret_key = 'security_secret_key_2024'
CORS(app)

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

SECURITY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Datacenters Security - Pi Datacenters</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .card h2 { color: #1e3c72; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        input, select, textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            text-align: center;
            border-radius: 10px;
        }
        .stat-card h3 { font-size: 12px; color: #666; text-transform: uppercase; }
        .stat-card p { font-size: 28px; font-weight: bold; color: #1e3c72; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn {
            background: rgba(255,255,255,0.9);
            color: #1e3c72;
            width: auto;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            border: none;
        }
        .tab-btn.active { background: #1e3c72; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .visitor-item {
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid #1e3c72;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge.in { background: #2196F3; color: white; }
        .badge.out { background: #9e9e9e; color: white; }
        .badge.approved { background: #4caf50; color: white; }
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
        }
        .btn-checkout { background: #4caf50; }
        .photo-preview {
            width: 200px;
            height: 200px;
            border: 2px dashed #ddd;
            border-radius: 10px;
            margin: 10px auto;
            overflow: hidden;
            background: #f9f9f9;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .photo-preview img { width: 100%; height: 100%; object-fit: cover; }
        .photo-preview .placeholder {
            color: #999;
            text-align: center;
        }
        .camera-btn { 
            background: #2196F3; 
            width: auto; 
            margin: 5px;
            padding: 10px 20px;
        }
        .camera-btn:hover { background: #1976D2; }
        video { 
            width: 100%; 
            max-width: 400px; 
            border-radius: 10px; 
            margin: 10px auto; 
            display: block;
            border: 2px solid #ddd;
        }
        .meeting-field { display: none; margin-top: 5px; }
        .meeting-field.show { display: block; }
        .top-bar {
            background: rgba(0,0,0,0.8);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-radius: 10px;
            color: white;
        }
        .logout-btn { width: auto; padding: 8px 20px; background: #f44336; }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 15px; display: none; }
        .alert-success { background: #d4edda; color: #155724; display: block; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; }
        .grid { display: grid; gap: 20px; grid-template-columns: 1fr 1fr; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .button-group {
            display: flex;
            gap: 10px;
            justify-content: center;
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
    </style>
</head>
<body>
    <div id="loginPage">
        <div class="container">
            <div class="card" style="max-width: 400px; margin: 50px auto;">
                <div class="logo-container">
                    {% if logo_base64 %}
                        <img src="{{ logo_base64 }}" alt="PI Data Centers Logo" class="logo-img">
                    {% else %}
                        <div style="font-size: 60px;">🔒</div>
                    {% endif %}
                    <h2 class="login-title">Pi Datacenters Security Login</h2>
                    <p class="login-subtitle">Authorized Personnel Only</p>
                </div>
                <div id="loginAlert" class="alert"></div>
                <input type="text" id="username" placeholder="Username">
                <input type="password" id="password" placeholder="Password">
                <button onclick="doLogin()">Login</button>
                <p style="text-align: center; margin-top: 15px;">
                    <a href="http://localhost:8080" style="color: #1e3c72;">← Back to Gateway</a>
                </p>
            </div>
        </div>
    </div>

    <div id="mainApp" style="display:none;">
        <div class="top-bar">
            <div class="brand">
                <strong>Pi Datacenters - Security Portal</strong>
            </div>
            <span>👤 <span id="currentUser"></span></span>
            <button class="logout-btn" onclick="doLogout()">Logout</button>
        </div>
        <div class="container">
            <h1 style="color: white;">Security Service</h1>
            <div style="color: white; text-align: center; margin-bottom: 20px;">Check-in / Check-out Management</div>
            
            <div class="tabs">
                <button class="tab-btn active" onclick="showTab('checkin')">✅ Check In</button>
                <button class="tab-btn" onclick="showTab('active')">🏢 Active Visitors</button>
                <button class="tab-btn" onclick="showTab('approved')">✅ Approved Appointments</button>
            </div>

            <div id="checkinTab" class="tab-content active">
                <div class="grid">
                    <div class="card">
                        <h2>Check In Visitor</h2>
                        <form id="checkinForm" onsubmit="return submitCheckin()">
                            <input type="text" id="name" placeholder="Full Name *" required>
                            <input type="email" id="email" placeholder="Email *" required>
                            <input type="tel" id="phone" placeholder="Phone *" required>
                            <input type="text" id="vehicle" placeholder="Vehicle Number">
                            <select id="purpose" required onchange="toggleMeetingField()">
                                <option value="">Select Purpose *</option>
                                <option value="Data Center Tour">Data Center Tour</option>
                                <option value="Meeting">Meeting</option>
                                <option value="Delivery">Delivery</option>
                                <option value="Maintenance">Maintenance</option>
                            </select>
                            <div id="meetingField" class="meeting-field">
                                <label>👤 Meeting With *</label>
                                <input type="text" id="meetingWith" placeholder="Enter person or department name">
                            </div>
                            <div class="photo-container">
                                <label>📸 Visitor Photo *</label>
                                <div class="photo-preview" id="photoPreview">
                                    <div class="placeholder">No photo captured</div>
                                </div>
                                <input type="hidden" id="visitorPhoto">
                                <div id="cameraContainer" style="display: none;">
                                    <video id="cameraVideo" autoplay playsinline></video>
                                    <canvas id="cameraCanvas" style="display:none;"></canvas>
                                </div>
                                <div class="button-group">
                                    <button type="button" class="camera-btn" onclick="startCamera()">📷 Start Camera</button>
                                    <button type="button" class="camera-btn" onclick="capturePhoto()" id="captureBtn" style="display:none;">📸 Capture</button>
                                    <button type="button" class="camera-btn" onclick="uploadPhoto()" id="uploadBtn">📁 Upload Photo</button>
                                </div>
                            </div>
                            <button type="submit">✅ Check In Visitor</button>
                        </form>
                    </div>
                    <div class="card">
                        <h2>📊 Quick Stats</h2>
                        <div class="stats">
                            <div class="stat-card"><h3>Inside Now</h3><p id="inside">0</p></div>
                            <div class="stat-card"><h3>Today's Check-ins</h3><p id="today">0</p></div>
                            <div class="stat-card"><h3>Today's Check-outs</h3><p id="checkedOut">0</p></div>
                        </div>
                        <div style="margin-top: 20px;">
                            <button onclick="location.reload()" style="background: #607d8b;">🔄 Refresh Data</button>
                        </div>
                    </div>
                </div>
            </div>

            <div id="activeTab" class="tab-content">
                <div class="card">
                    <h2>Active Visitors (Currently Inside)</h2>
                    <div id="activeList"></div>
                </div>
            </div>

            <div id="approvedTab" class="tab-content">
                <div class="card">
                    <h2>✅ Approved Appointments</h2>
                    <p style="color: #666; margin-bottom: 15px;">These visitors have been approved by admin and can be checked in</p>
                    <div id="approvedList"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let cameraStream = null;
        let videoElement = null;
        let canvasElement = null;

        async function api(url, method='GET', data=null) {
            const opts = { method, headers: {'Content-Type': 'application/json'}};
            if (data) opts.body = JSON.stringify(data);
            try {
                const res = await fetch(url, opts);
                return await res.json();
            } catch(e) {
                console.error('API Error:', e);
                return null;
            }
        }

        function toggleMeetingField() {
            const purpose = document.getElementById('purpose').value;
            const meetingField = document.getElementById('meetingField');
            if (purpose === 'Meeting') {
                meetingField.classList.add('show');
            } else {
                meetingField.classList.remove('show');
                document.getElementById('meetingWith').value = '';
            }
        }

        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            if (!username || !password) { alert('Enter credentials'); return; }
            
            const result = await api('/api/login', 'POST', { username, password });
            if (result && result.success) {
                currentUser = result.username;
                sessionStorage.setItem('security_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadAllData();
                initializeCamera();
            } else {
                alert('Invalid credentials or unauthorized access');
            }
        }

        function doLogout() {
            currentUser = null;
            sessionStorage.removeItem('security_user');
            stopCamera();
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
        }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tab + 'Tab').classList.add('active');
            if (tab === 'active') loadActiveVisitors();
            if (tab === 'approved') loadApprovedAppointments();
        }

        async function loadAllData() {
            await loadStats();
            await loadActiveVisitors();
            await loadApprovedAppointments();
        }

        async function loadStats() {
            const stats = await api('/api/stats');
            if (stats) {
                document.getElementById('inside').textContent = stats.inside || 0;
                document.getElementById('today').textContent = stats.today || 0;
                document.getElementById('checkedOut').textContent = stats.checkedOutToday || 0;
            }
        }

        async function loadActiveVisitors() {
            const visitors = await api('/api/visitors?status=in');
            const container = document.getElementById('activeList');
            if (!visitors || visitors.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:#999;padding:20px;">No visitors inside</p>';
                return;
            }
            container.innerHTML = visitors.map(v => `
                <div class="visitor-item">
                    <strong>${escapeHtml(v.name)}</strong><br>
                    📧 ${escapeHtml(v.email)} | 📞 ${escapeHtml(v.phone)}<br>
                    🚗 ${escapeHtml(v.vehicle_number || 'N/A')} | 📝 ${escapeHtml(v.purpose)}<br>
                    ${v.meeting_with ? '👤 Meeting: ' + escapeHtml(v.meeting_with) + '<br>' : ''}
                    🕐 ${v.check_in_time}<br>
                    ${v.photo ? '<img src="' + v.photo + '" style="width:50px;height:50px;border-radius:50%;margin-top:5px;">' : ''}<br>
                    <span class="badge in">INSIDE</span><br>
                    <button class="btn-small btn-checkout" onclick="checkoutVisitor('${v.visitor_id || v.id}')">🚪 Check Out</button>
                </div>
            `).join('');
        }

        async function loadApprovedAppointments() {
            const apps = await api('/api/appointments?status=approved');
            const container = document.getElementById('approvedList');
            if (!apps || apps.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:#999;padding:20px;">No approved appointments</p>';
                return;
            }
            container.innerHTML = apps.map(a => `
                <div class="visitor-item" style="border-left-color: #4caf50;">
                    <strong>${escapeHtml(a.name)}</strong><br>
                    📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                    📝 ${escapeHtml(a.purpose)}<br>
                    ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                    📅 ${a.appointment_date}<br>
                    <span class="badge approved">APPROVED</span><br>
                    <button class="btn-small btn-checkout" onclick="checkInFromAppointment('${a.appointment_id || a.id}')">✅ Check In Now</button>
                </div>
            `).join('');
        }

        async function checkInFromAppointment(appointmentId) {
            const appt = await api(`/api/appointments/${appointmentId}`);
            if (appt) {
                document.getElementById('name').value = appt.name;
                document.getElementById('email').value = appt.email;
                document.getElementById('phone').value = appt.phone;
                document.getElementById('vehicle').value = appt.vehicle_number || '';
                document.getElementById('purpose').value = appt.purpose;
                if (appt.meeting_with) {
                    document.getElementById('meetingWith').value = appt.meeting_with;
                    toggleMeetingField();
                }
                showTab('checkin');
                alert('Visitor data loaded. Please capture photo and complete check-in.');
            }
        }

        async function checkoutVisitor(id) {
            if (!confirm('Check out this visitor?')) return;
            const result = await api('/api/visitors/' + id + '/checkout', 'PUT', { checked_out_by: currentUser });
            if (result && result.success) {
                alert('✅ Visitor checked out successfully!');
                loadAllData();
            } else {
                alert('❌ Checkout failed');
            }
        }

        function initializeCamera() {
            videoElement = document.getElementById('cameraVideo');
            canvasElement = document.getElementById('cameraCanvas');
        }

        async function startCamera() {
            const cameraContainer = document.getElementById('cameraContainer');
            const captureBtn = document.getElementById('captureBtn');
            const startCameraBtn = document.querySelector('.camera-btn');
            
            try {
                if (cameraStream) {
                    stopCamera();
                }
                cameraStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'user' } 
                });
                videoElement.srcObject = cameraStream;
                cameraContainer.style.display = 'block';
                captureBtn.style.display = 'inline-block';
                startCameraBtn.style.display = 'none';
                await videoElement.play();
            } catch (err) {
                console.error('Camera error:', err);
                alert('Unable to access camera. Please use upload option.');
                cameraContainer.style.display = 'none';
            }
        }

        function stopCamera() {
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
                cameraStream = null;
            }
            if (videoElement) {
                videoElement.srcObject = null;
            }
            const cameraContainer = document.getElementById('cameraContainer');
            const captureBtn = document.getElementById('captureBtn');
            const startCameraBtn = document.querySelector('.camera-btn');
            if (cameraContainer) cameraContainer.style.display = 'none';
            if (captureBtn) captureBtn.style.display = 'none';
            if (startCameraBtn) startCameraBtn.style.display = 'inline-block';
        }

        function capturePhoto() {
            if (!videoElement || !videoElement.videoWidth) {
                alert('Camera not ready. Please start camera first.');
                return;
            }
            
            canvasElement.width = videoElement.videoWidth;
            canvasElement.height = videoElement.videoHeight;
            const context = canvasElement.getContext('2d');
            context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            
            const photoData = canvasElement.toDataURL('image/jpeg', 0.8);
            document.getElementById('visitorPhoto').value = photoData;
            
            const preview = document.getElementById('photoPreview');
            preview.innerHTML = `<img src="${photoData}" alt="Visitor Photo">`;
            
            stopCamera();
            alert('✅ Photo captured successfully!');
        }

        function uploadPhoto() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/jpeg, image/png, image/jpg';
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        const photoData = event.target.result;
                        document.getElementById('visitorPhoto').value = photoData;
                        const preview = document.getElementById('photoPreview');
                        preview.innerHTML = `<img src="${photoData}" alt="Visitor Photo">`;
                        alert('✅ Photo uploaded successfully!');
                    };
                    reader.readAsDataURL(file);
                }
            };
            input.click();
        }

        async function submitCheckin() {
            event.preventDefault();
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const purpose = document.getElementById('purpose').value;
            const photo = document.getElementById('visitorPhoto').value;
            const meetingWith = document.getElementById('meetingWith').value.trim();
            
            if (!name || !email || !phone || !purpose) {
                alert('⚠️ Please fill all required fields');
                return false;
            }
            
            if (!photo) {
                alert('⚠️ Please capture or upload a photo before check-in');
                return false;
            }
            
            if (purpose === 'Meeting' && !meetingWith) {
                alert('⚠️ Please enter who you are meeting with');
                return false;
            }
            
            const result = await api('/api/visitors', 'POST', {
                name, email, phone,
                vehicle_number: document.getElementById('vehicle').value.trim(),
                purpose, meeting_with: meetingWith, photo, checked_in_by: currentUser
            });
            
            if (result && result.success) {
                document.getElementById('checkinForm').reset();
                document.getElementById('visitorPhoto').value = '';
                document.getElementById('photoPreview').innerHTML = '<div class="placeholder">No photo captured</div>';
                document.getElementById('meetingField').classList.remove('show');
                loadAllData();
                showTab('active');
                alert('✅ Visitor checked in successfully!');
            } else {
                alert('❌ Check-in failed. Please try again.');
            }
            return false;
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        const savedUser = sessionStorage.getItem('security_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadAllData();
            initializeCamera();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    return render_template_string(SECURITY_TEMPLATE, logo_base64=logo_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'security', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='security'", 
                         (data['username'], data['password']))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return jsonify({'success': True, 'username': user['username'], 'role': user['role']})
        except Exception as e:
            print(f"Login error: {e}")
    return jsonify({'success': False}), 401

@app.route('/api/visitors', methods=['GET'])
def get_visitors():
    status = request.args.get('status', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM visitors"
            params = []
            if status:
                query += " WHERE status=%s"
                params.append(status)
            query += " ORDER BY check_in_time DESC"
            cursor.execute(query, params)
            visitors = cursor.fetchall()
            cursor.close()
            conn.close()
            for v in visitors:
                if v.get('check_in_time'):
                    v['check_in_time'] = str(v['check_in_time'])
                if v.get('check_out_time'):
                    v['check_out_time'] = str(v['check_out_time'])
            return jsonify(visitors)
        except Exception as e:
            print(f"Error: {e}")
    return jsonify([])

@app.route('/api/visitors', methods=['POST'])
def add_visitor():
    data = request.json
    visitor_id = str(uuid.uuid4())[:8]
    check_in_time = datetime.now()
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO visitors (visitor_id, name, email, phone, vehicle_number, purpose, meeting_with, photo, check_in_time, status, checked_in_by) 
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                          (visitor_id, data['name'], data['email'], data['phone'], data.get('vehicle_number',''), 
                           data['purpose'], data.get('meeting_with',''), data.get('photo',''), check_in_time, 'in', data.get('checked_in_by','security')))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Visitor added: {data['name']}")
            return jsonify({'success': True, 'visitor_id': visitor_id})
        except Exception as e:
            print(f"Error adding visitor: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Failed'}), 500

@app.route('/api/visitors/<vid>/checkout', methods=['PUT'])
def checkout(vid):
    checkout_time = datetime.now()
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE visitors SET check_out_time=%s, status='out', checked_out_by=%s WHERE visitor_id=%s AND status='in'", 
                         (checkout_time, request.json.get('checked_out_by', 'security'), vid))
            if cursor.rowcount == 0:
                cursor.execute("UPDATE visitors SET check_out_time=%s, status='out', checked_out_by=%s WHERE id=%s AND status='in'", 
                             (checkout_time, request.json.get('checked_out_by', 'security'), vid))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error checking out: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Failed'}), 500

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    status = request.args.get('status', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM appointments"
            params = []
            if status:
                query += " WHERE status=%s"
                params.append(status)
            query += " ORDER BY appointment_date ASC"
            cursor.execute(query, params)
            apps = cursor.fetchall()
            cursor.close()
            conn.close()
            for a in apps:
                if a.get('appointment_date'):
                    a['appointment_date'] = str(a['appointment_date'])
            return jsonify(apps)
        except Exception as e:
            print(f"Error: {e}")
    return jsonify([])

@app.route('/api/appointments/<aid>', methods=['GET'])
def get_appointment(aid):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE appointment_id=%s OR id=%s", (aid, aid))
            appt = cursor.fetchone()
            cursor.close()
            conn.close()
            if appt and appt.get('appointment_date'):
                appt['appointment_date'] = str(appt['appointment_date'])
            return jsonify(appt)
        except Exception as e:
            print(f"Error: {e}")
    return jsonify(None)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE status='in'")
            inside = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE DATE(check_in_time)=CURDATE()")
            today = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE DATE(check_out_time)=CURDATE() AND status='out'")
            checked_out = cursor.fetchone()['c']
            cursor.close()
            conn.close()
            return jsonify({'inside': inside, 'today': today, 'checkedOutToday': checked_out})
        except Exception as e:
            print(f"Error: {e}")
    return jsonify({'inside': 0, 'today': 0, 'checkedOutToday': 0})

if __name__ == '__main__':
    print("🔒 Security Service running on port 8081")
    print("   URL: http://localhost:8081")
    print("   Login: security / security123")
    print("   Photo capture: Start camera → Capture → Check-in")
    app.run(host='0.0.0.0', port=8081, debug=False)
