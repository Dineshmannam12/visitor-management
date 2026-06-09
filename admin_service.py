from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_logo_base64, COMPANY_NAME, EMAIL_CONFIG

app = Flask(__name__)
app.secret_key = 'admin_secret_key_2024'
CORS(app)

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

def send_email(to_email, subject, body):
    """Send email using SMTP configuration"""
    if not to_email or to_email == 'string':
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
    """Get manager email from settings"""
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key='manager_email'")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result and result['setting_value'] and result['setting_value'] != 'string':
                return result['setting_value']
        except Exception as e:
            print(f"Error getting manager email: {e}")
    return None

def get_all_admin_emails():
    """Get all admin and manager emails for notifications"""
    emails = []
    
    # Add manager email
    manager_email = get_manager_email()
    if manager_email:
        emails.append(manager_email)
    
    # Get additional emails from settings
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
    
    # Remove duplicates and invalid emails
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
        button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn {
            background: rgba(255,255,255,0.9);
            color: #1e3c72;
            width: auto;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
        }
        .tab-btn.active { background: #1e3c72; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .visitor-item {
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid #ff9800;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge.pending { background: #ff9800; color: white; }
        .badge.approved { background: #4caf50; color: white; }
        .badge.rejected { background: #f44336; color: white; }
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
        .btn-approve { background: #4caf50; }
        .btn-reject { background: #f44336; }
        .btn-undo { background: #ff9800; }
        .btn-delete { background: #f44336; }
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
        .stat-card p { font-size: 28px; font-weight: bold; color: #1e3c72; }
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
        .logout-btn { background: #f44336; }
        input, textarea {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
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
        }
        .alert-success { background: #d4edda; color: #155724; display: block; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; }
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
                        <div style="font-size: 60px;">👑</div>
                    {% endif %}
                    <h2 class="login-title">Pi Admin Login</h2>
                    <p class="login-subtitle">Administrator Access Only</p>
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
            <div class="brand"><strong>PI Data Centers - Admin Portal</strong></div>
            <span>👤 <span id="currentUser"></span></span>
            <button class="logout-btn" onclick="doLogout()">Logout</button>
        </div>
        <div class="container">
            <h1 style="color: white;">👑 Admin Service</h1>
            <div style="color: white; text-align: center; margin-bottom: 20px;">Approve/Reject Visitor Requests</div>
            
            <div class="tabs">
                <button class="tab-btn active" onclick="showTab('pending')">⏳ Pending Approvals</button>
                <button class="tab-btn" onclick="showTab('approved')">✅ Approved</button>
                <button class="tab-btn" onclick="showTab('rejected')">❌ Rejected</button>
                <button class="tab-btn" onclick="showTab('settings')">⚙️ Settings</button>
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
                    <button onclick="saveSettings()">Save Settings</button>
                    <div id="settingsAlert" class="alert" style="margin-top: 15px;"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="notificationAlert" class="alert" style="display:none;"></div>

    <script>
        let currentUser = null;

        async function api(url, method='GET', data=null) {
            const opts = { method, headers: {'Content-Type': 'application/json'}};
            if (data) opts.body = JSON.stringify(data);
            try {
                const res = await fetch(url, opts);
                const text = await res.text();
                try {
                    return JSON.parse(text);
                } catch(e) {
                    console.error('Invalid JSON:', text);
                    return null;
                }
            } catch(e) {
                console.error('API Error:', e);
                return null;
            }
        }

        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const result = await api('/api/login', 'POST', { username, password });
            if (result && result.success && result.role === 'admin') {
                currentUser = result.username;
                sessionStorage.setItem('admin_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadAllData();
                loadSettings();
            } else {
                alert('Invalid credentials or unauthorized access');
            }
        }

        function doLogout() {
            currentUser = null;
            sessionStorage.removeItem('admin_user');
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
        }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tab + 'Tab').classList.add('active');
            if (tab === 'pending') loadPendingAppointments();
            if (tab === 'approved') loadApprovedAppointments();
            if (tab === 'rejected') loadRejectedAppointments();
        }

        async function loadAllData() {
            await loadPendingAppointments();
            await loadApprovedAppointments();
            await loadRejectedAppointments();
        }

        async function loadPendingAppointments() {
            const apps = await api('/api/appointments?status=pending');
            const container = document.getElementById('pendingList');
            if (!apps || apps.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:#999;padding:20px;">No pending requests</p>';
                return;
            }
            container.innerHTML = apps.map(a => `
                <div class="visitor-item">
                    <strong>${escapeHtml(a.name)}</strong><br>
                    📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                    🚗 ${escapeHtml(a.vehicle_number || 'N/A')}<br>
                    📝 ${escapeHtml(a.purpose)}<br>
                    ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                    📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                    📝 Notes: ${escapeHtml(a.notes || 'N/A')}<br>
                    <span class="badge pending">PENDING</span><br>
                    <button class="btn-small btn-approve" onclick="approveAppt('${a.appointment_id || a.id}')">✅ Approve</button>
                    <button class="btn-small btn-reject" onclick="rejectAppt('${a.appointment_id || a.id}')">❌ Reject</button>
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
                <div class="visitor-item" style="border-left-color:#4caf50;">
                    <strong>${escapeHtml(a.name)}</strong><br>
                    📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                    📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                    <span class="badge approved">APPROVED</span><br>
                    <button class="btn-small btn-undo" onclick="undoAppt('${a.appointment_id || a.id}')">↩ Undo</button>
                    <button class="btn-small btn-delete" onclick="deleteAppt('${a.appointment_id || a.id}')">🗑 Delete</button>
                </div>
            `).join('');
        }

        async function loadRejectedAppointments() {
            const apps = await api('/api/appointments?status=rejected');
            const container = document.getElementById('rejectedList');
            if (!apps || apps.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:#999;padding:20px;">No rejected appointments</p>';
                return;
            }
            container.innerHTML = apps.map(a => `
                <div class="visitor-item" style="border-left-color:#f44336;">
                    <strong>${escapeHtml(a.name)}</strong><br>
                    📧 ${escapeHtml(a.email)}<br>
                    📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                    <div class="rejection-reason">
                        ❌ Rejection Reason: ${escapeHtml(a.rejection_reason || 'Not specified')}
                    </div>
                    <span class="badge rejected">REJECTED</span><br>
                    <button class="btn-small btn-undo" onclick="undoAppt('${a.appointment_id || a.id}')">↩ Undo</button>
                    <button class="btn-small btn-delete" onclick="deleteAppt('${a.appointment_id || a.id}')">🗑 Delete</button>
                </div>
            `).join('');
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
                loadAllData();
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
            
            // First update the status
            const result = await api('/api/appointments/' + id + '/status', 'PUT', { 
                status: 'rejected', 
                rejection_reason: reason 
            });
            
            if (result && result.success) {
                // Then send rejection emails
                const emailResult = await api('/api/email/rejection', 'POST', { 
                    appointment_id: id, 
                    reason: reason 
                });
                
                if (emailResult && emailResult.success) {
                    showNotification('❌ Rejected! Visitor and staff have been notified via email.', 'success');
                } else {
                    showNotification('❌ Rejected! But email notification failed. Please check email settings.', 'warning');
                }
                loadAllData();
            } else {
                showNotification('❌ Failed to reject. Please try again. Error: ' + (result?.error || 'Unknown'), 'error');
            }
        }

        async function undoAppt(id) {
            if (!confirm('Undo this action? This will set the status back to pending.')) return;
            const result = await api('/api/appointments/' + id + '/status', 'PUT', { status: 'pending' });
            if (result && result.success) {
                showNotification('✅ Status reset to pending!', 'success');
                loadAllData();
            } else {
                showNotification('❌ Failed to undo. Please try again.', 'error');
            }
        }

        async function deleteAppt(id) {
            if (!confirm('Delete this appointment permanently?')) return;
            const result = await api('/api/appointments/' + id, 'DELETE');
            if (result && result.success) {
                showNotification('✅ Appointment deleted!', 'success');
                loadAllData();
            } else {
                showNotification('❌ Failed to delete. Please try again.', 'error');
            }
        }

        async function loadSettings() {
            const manager = await api('/api/settings/manager_email');
            const additional = await api('/api/settings/additional_emails');
            if (manager && manager.value) document.getElementById('managerEmail').value = manager.value;
            if (additional && additional.value) document.getElementById('additionalEmails').value = additional.value;
        }

        async function saveSettings() {
            const managerEmail = document.getElementById('managerEmail').value.trim();
            const additionalEmails = document.getElementById('additionalEmails').value.trim();
            await api('/api/settings/manager_email', 'POST', { value: managerEmail });
            await api('/api/settings/additional_emails', 'POST', { value: additionalEmails });
            showNotification('✅ Settings saved successfully!', 'success');
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

        const savedUser = sessionStorage.getItem('admin_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadAllData();
            loadSettings();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    return render_template_string(ADMIN_TEMPLATE, logo_base64=logo_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'admin', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'", 
                         (data['username'], data['password']))
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
            query = "SELECT * FROM appointments"
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
    if new_status == 'rejected':
        print(f"   Rejection reason: {rejection_reason}")
    
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            if new_status == 'rejected':
                cursor.execute("""UPDATE appointments 
                               SET status=%s, rejection_reason=%s 
                               WHERE appointment_id=%s OR id=%s""", 
                             (new_status, rejection_reason, aid, aid))
            else:
                cursor.execute("""UPDATE appointments 
                               SET status=%s 
                               WHERE appointment_id=%s OR id=%s""", 
                             (new_status, aid, aid))
            
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
            
            # Send email to visitor
            visitor_subject = f"✅ Your Visit to {COMPANY_NAME} has been APPROVED!"
            visitor_body = f"""
Dear {appt['name']},

We are pleased to inform you that your visit request to {COMPANY_NAME} has been APPROVED.

📋 Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
• Vehicle: {appt.get('vehicle_number', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: APPROVED

Important Instructions:
1. Please bring a valid government-issued ID
2. Report to the security desk upon arrival
3. Security will check you in using your name/email

Thank you for choosing {COMPANY_NAME}.

Best regards,
{COMPANY_NAME} Management
"""
            send_email(appt['email'], visitor_subject, visitor_body)
            
            # Also notify managers about approval
            admin_emails = get_all_admin_emails()
            if admin_emails:
                admin_subject = f"✅ Appointment APPROVED - {appt['name']}"
                admin_body = f"""
APPOINTMENT APPROVED ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The following appointment has been APPROVED:

📋 Visitor Details:
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}

✅ Status: APPROVED

This visitor has been notified and will check in at security.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
                for email in admin_emails:
                    send_email(email, admin_subject, admin_body)
            
            return jsonify({'success': True})
        except Exception as e:
            print(f"Approval email error: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': False}), 500

@app.route('/api/email/rejection', methods=['POST'])
def email_rejection():
    data = request.json
    aid = data.get('appointment_id', '')
    reason = data.get('reason', 'Your request did not meet our approval criteria.')
    
    print(f"📧 Sending rejection email for appointment: {aid}")
    print(f"   Reason: {reason}")
    
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE appointment_id=%s OR id=%s", (aid, aid))
            appt = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not appt:
                print(f"❌ Appointment not found: {aid}")
                return jsonify({'success': False, 'error': 'Appointment not found'}), 404
            
            print(f"✅ Found appointment for: {appt['name']} ({appt['email']})")
            
            meeting_text = f"\n- Meeting With: {appt.get('meeting_with', 'N/A')}" if appt.get('meeting_with') else ''
            
            # 1. Send rejection email to the visitor
            visitor_subject = f"❌ Your Visit to {COMPANY_NAME} has been REJECTED"
            visitor_body = f"""
Dear {appt['name']},

We regret to inform you that your visit request to {COMPANY_NAME} has been REJECTED.

📋 Request Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}
• Vehicle: {appt.get('vehicle_number', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Rejection Reason:
{reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you believe this is an error or need to reschedule, please contact us.

We appreciate your understanding.

Best regards,
{COMPANY_NAME} Management
"""
            visitor_email_sent = send_email(appt['email'], visitor_subject, visitor_body)
            
            # 2. Send notification to all managers/admins about rejection
            admin_emails = get_all_admin_emails()
            
            if admin_emails:
                admin_subject = f"❌ Appointment REJECTED - {appt['name']}"
                admin_body = f"""
APPOINTMENT REJECTED ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The following appointment has been REJECTED:

📋 Visitor Details:
• Name: {appt['name']}
• Email: {appt['email']}
• Phone: {appt['phone']}
• Purpose: {appt['purpose']}{meeting_text}
• Date & Time: {appt['appointment_date']}

❌ Rejection Reason:
{reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The visitor has been notified of this decision.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
                for email in admin_emails:
                    send_email(email, admin_subject, admin_body)
            
            return jsonify({
                'success': True, 
                'visitor_notified': visitor_email_sent,
                'admin_notified': len(admin_emails) > 0
            })
            
        except Exception as e:
            print(f"❌ Rejection email error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

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
            if result and result['setting_value']:
                return jsonify({'value': result['setting_value']})
        except Exception as e:
            print(f"Error getting setting: {e}")
    return jsonify({'value': None})

@app.route('/api/settings/<key>', methods=['POST'])
def set_setting(key):
    data = request.json
    value = data.get('value', '')
    
    # Don't save invalid values
    if value == 'string' or value == 'null' or value == 'undefined':
        value = ''
    
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET setting_value=%s WHERE setting_key=%s", (value, key))
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s,%s)", (key, value))
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
    app.run(host='0.0.0.0', port=8082, debug=False)
