from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_logo_base64, COMPANY_NAME, EMAIL_CONFIG

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

def send_email(to_email, subject, body):
    """Send email using SMTP configuration"""
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
        print(f"❌ Email error: {e}")
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
            if result and result['setting_value']:
                return result['setting_value']
        except Exception as e:
            print(f"Error getting manager email: {e}")
    return 'manager@pidatacenters.com'

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
                additional = [e.strip() for e in result['setting_value'].split(',') if e.strip() and '@' in e]
                emails.extend(additional)
        except Exception as e:
            print(f"Error getting additional emails: {e}")
    
    # Also get admin users
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email FROM users WHERE role='admin' AND email IS NOT NULL AND email != ''")
            admin_emails = cursor.fetchall()
            cursor.close()
            conn.close()
            for admin in admin_emails:
                if admin['email'] and admin['email'] not in emails:
                    emails.append(admin['email'])
        except Exception as e:
            print(f"Error getting admin emails: {e}")
    
    return list(set(emails))  # Remove duplicates

VISITOR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visitor Pre-Registration - Pi Datacenters</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
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
        .meeting-field { display: none; margin-top: 5px; }
        .meeting-field.show { display: block; }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: none;
        }
        .alert-success { background: #d4edda; color: #155724; display: block; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; }
        .status-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
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
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: white;
            text-decoration: none;
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
        .page-title {
            color: #1e3c72;
            font-size: 24px;
            margin-top: 10px;
        }
        .page-subtitle {
            color: #666;
            font-size: 14px;
        }
        .info-box {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 13px;
            color: #1976d2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo-container">
                {% if logo_base64 %}
                    <img src="{{ logo_base64 }}" alt="PI Data Centers Logo" class="logo-img">
                {% else %}
                    <div style="font-size: 50px;">📝</div>
                {% endif %}
                <h2 class="page-title">Pi Datacenters - Visitor Pre-Registration</h2>
                <p class="page-subtitle">Please fill in your details to pre-register your visit</p>
            </div>
            
            <div class="info-box">
                ℹ️ After submission, our team will review your request and send an approval email.
            </div>
            
            <div id="alert" class="alert"></div>
            
            <form id="registerForm" onsubmit="return submitRegistration()">
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
                <label>Appointment Date & Time *</label>
                <input type="datetime-local" id="appointmentDate" required>
                <textarea id="notes" rows="3" placeholder="Additional Notes (Optional)"></textarea>
                <button type="submit">📤 Submit Registration</button>
            </form>
        </div>

        <div class="card">
            <h2 style="color: #1e3c72; margin-bottom: 20px; text-align: center;">🔍 Check Registration Status</h2>
            <p style="color: #666; font-size: 13px; margin-bottom: 15px; text-align: center;">Enter your email to check the status of your registration</p>
            <input type="email" id="checkEmail" placeholder="Enter your email">
            <button onclick="checkStatus()">Check Status</button>
            <div id="statusResult" class="status-card" style="display:none;"></div>
        </div>
        
        <div class="back-link">
            <a href="http://localhost:8080">← Back to Gateway</a>
        </div>
    </div>

    <script>
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

        async function submitRegistration() {
            event.preventDefault();
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const purpose = document.getElementById('purpose').value;
            const meetingWith = document.getElementById('meetingWith').value.trim();
            const appointmentDate = document.getElementById('appointmentDate').value;
            const notes = document.getElementById('notes').value.trim();
            
            if (!name || !email || !phone || !purpose) {
                showAlert('Please fill all required fields', 'error');
                return false;
            }
            
            if (purpose === 'Meeting' && !meetingWith) {
                showAlert('Please enter who you are meeting with', 'error');
                return false;
            }
            
            if (!appointmentDate) {
                showAlert('Please select appointment date and time', 'error');
                return false;
            }
            
            // Show loading state
            const submitBtn = event.target.querySelector('button');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;
            
            const result = await api('/api/appointments', 'POST', {
                name, email, phone,
                vehicle_number: document.getElementById('vehicle').value.trim(),
                purpose, meeting_with: meetingWith,
                appointment_date: appointmentDate,
                notes: notes,
                created_by: 'visitor'
            });
            
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            
            if (result && result.success) {
                showAlert('✅ Registration submitted successfully! You will receive an email confirmation once approved.', 'success');
                document.getElementById('registerForm').reset();
                document.getElementById('meetingField').classList.remove('show');
            } else {
                showAlert('❌ Registration failed. Please try again.', 'error');
            }
            return false;
        }

        async function checkStatus() {
            const email = document.getElementById('checkEmail').value.trim();
            if (!email) {
                showAlert('Please enter your email', 'error');
                return;
            }
            
            const apps = await api('/api/appointments/check?email=' + encodeURIComponent(email));
            const resultDiv = document.getElementById('statusResult');
            
            if (!apps || apps.length === 0) {
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = '<p style="color:#666;">No registrations found for this email.</p>';
                return;
            }
            
            let html = '<h3 style="margin-bottom:15px;">Your Registrations:</h3>';
            apps.forEach(a => {
                let statusBadge = '';
                if (a.status === 'pending') {
                    statusBadge = '<span class="badge pending">⏳ PENDING</span>';
                } else if (a.status === 'approved') {
                    statusBadge = '<span class="badge approved">✅ APPROVED</span>';
                } else {
                    statusBadge = '<span class="badge rejected">❌ REJECTED</span>';
                }
                
                html += `
                    <div style="border-top:1px solid #ddd; padding:10px 0;">
                        <p><strong>📅 Date:</strong> ${new Date(a.appointment_date).toLocaleString()}</p>
                        <p><strong>📝 Purpose:</strong> ${escapeHtml(a.purpose)}</p>
                        <p><strong>📊 Status:</strong> ${statusBadge}</p>
                        ${a.rejection_reason ? '<p><strong>❌ Reason:</strong> ' + escapeHtml(a.rejection_reason) + '</p>' : ''}
                    </div>
                `;
            });
            
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = html;
        }

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

        function showAlert(msg, type) {
            const alertDiv = document.getElementById('alert');
            alertDiv.textContent = msg;
            alertDiv.className = 'alert alert-' + type;
            setTimeout(() => {
                alertDiv.className = 'alert';
                alertDiv.style.display = 'none';
            }, 5000);
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Set default datetime to now + 1 hour
        const now = new Date();
        now.setHours(now.getHours() + 1);
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById('appointmentDate').value = now.toISOString().slice(0, 16);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    return render_template_string(VISITOR_TEMPLATE, logo_base64=logo_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'visitor', 'timestamp': datetime.now().isoformat()})

@app.route('/api/appointments', methods=['POST'])
def add_appointment():
    data = request.json
    appointment_id = str(uuid.uuid4())[:8]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO appointments (appointment_id, name, email, phone, vehicle_number, purpose, meeting_with, appointment_date, notes, status, created_by) 
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                          (appointment_id, data['name'], data['email'], data['phone'], data.get('vehicle_number',''), 
                           data['purpose'], data.get('meeting_with',''), data['appointment_date'], data.get('notes',''), 
                           'pending', data.get('created_by','visitor')))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Send email notifications
            send_registration_notifications(data, appointment_id)
            
            return jsonify({'success': True, 'appointment_id': appointment_id})
        except Exception as e:
            print(f"Error adding appointment: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Failed'}), 500

def send_registration_notifications(data, appointment_id):
    """Send email notifications to managers and admins"""
    
    # 1. Send confirmation email to the visitor
    visitor_subject = f"📅 Registration Received - {COMPANY_NAME}"
    visitor_body = f"""
Dear {data['name']},

Thank you for registering your visit to {COMPANY_NAME}.

Your registration has been received and is pending approval.

📋 Registration Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Registration ID: {appointment_id}
• Name: {data['name']}
• Email: {data['email']}
• Phone: {data['phone']}
• Purpose: {data['purpose']}
{f'• Meeting With: {data["meeting_with"]}' if data.get('meeting_with') else ''}
• Date & Time: {data['appointment_date']}
{f'• Notes: {data["notes"]}' if data.get('notes') else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Status: PENDING APPROVAL

You will receive another email once your visit is approved or rejected.

Please bring a valid government-issued ID when you arrive.

Thank you,
{COMPANY_NAME} Management
"""
    send_email(data['email'], visitor_subject, visitor_body)
    
    # 2. Send notification to all managers and admins
    admin_emails = get_all_admin_emails()
    
    if admin_emails:
        admin_subject = f"🔔 New Visitor Registration - {data['name']}"
        admin_body = f"""
NEW VISITOR REGISTRATION ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A new visitor has registered for a visit to {COMPANY_NAME}.

📋 Registration Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Registration ID: {appointment_id}
• Name: {data['name']}
• Email: {data['email']}
• Phone: {data['phone']}
• Vehicle: {data.get('vehicle_number', 'N/A')}
• Purpose: {data['purpose']}
{f'• Meeting With: {data["meeting_with"]}' if data.get('meeting_with') else ''}
• Date & Time: {data['appointment_date']}
{f'• Notes: {data["notes"]}' if data.get('notes') else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Status: PENDING APPROVAL

🔗 Action Required:
Please log in to the Admin Portal to review and approve/reject this request.

Admin Portal: http://localhost:8082

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
        
        for email in admin_emails:
            send_email(email, admin_subject, admin_body)
        print(f"✅ Notifications sent to {len(admin_emails)} admin/manager recipients")
    else:
        print("⚠️ No admin emails configured. Please set up email settings in Admin Portal.")
    
    # 3. Also send a test notification (optional)
    print(f"📧 Registration notification sent for {data['name']}")

@app.route('/api/appointments/check', methods=['GET'])
def check_appointments():
    email = request.args.get('email', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE email=%s ORDER BY appointment_date DESC", (email,))
            apps = cursor.fetchall()
            cursor.close()
            conn.close()
            for a in apps:
                if a.get('appointment_date'):
                    a['appointment_date'] = str(a['appointment_date'])
            return jsonify(apps)
        except Exception as e:
            print(f"Error checking appointments: {e}")
    return jsonify([])

if __name__ == '__main__':
    print("=" * 60)
    print("📝 Visitor Service running on port 8083")
    print("   URL: http://localhost:8083")
    print("   Features: Visitor Registration, Status Check, Email Notifications")
    print("   Email notifications sent to:")
    print("     - Visitor (confirmation email)")
    print("     - All managers/admins (notification email)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8083, debug=False)
