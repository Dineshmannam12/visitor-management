from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_logo_base64, COMPANY_NAME, EMAIL_CONFIG
import traceback
import json

app = Flask(__name__)
CORS(app)

# Authorised persons mapping with emails (for notification purposes only)
AUTHORISED_PERSONS = {
    'Mr. Abhinav Kotagiri': 'mannamvenkatadinesh@gmail.com'
}

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
    }
}

# Meeting person mapping with emails
MEETING_PERSON_MAP = {
    'Mr.KVS Prakasa Rao': ('karumudinikhil15@gmail.com', 'Mr.KVS Prakasa Rao'),
    'Mr.Manoj Muppaneni': ('manoj@pidatacenters.com', 'Mr.Manoj Muppaneni'),
    'Mr.Abhinav Kotagiri': ('abhinav.kotagiri@pidatacenters.com', 'Mr. Abhinav Kotagiri'),
    'Mr.Sreekanth Vattipally': ('srikanth@pidatacenters.com', 'Mr.Sreekanth vattipally'),
    'Mr.Haneesh Kumar': ('haneesh@pidatacenters.com', 'Mr.Haneesh kumar'),
    'Mr.Kalyan Muppaneni': ('kalyan@pidatacenters.com', 'Mr.Kalyan Muppaneni'),
    'Ms.Swapna Lopelly': ('swapna@pidatacenters.com', 'Ms.Swapna Lopally')
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

def get_all_notification_emails():
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

def send_registration_notification(visitor_data, appointment_id):
    meeting_text = f"\n- Meeting With: {visitor_data.get('meeting_with', 'N/A')}" if visitor_data.get('meeting_with') else ''
    company_text = f"\n- Company: {visitor_data.get('company_name', 'N/A')}" if visitor_data.get('company_name') else ''

    admin_emails = get_all_notification_emails()

    if admin_emails:
        admin_subject = f"🔔 New Visitor Registration - {visitor_data['name']}"
        admin_body = f"""
NEW VISITOR REGISTRATION ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A new visitor has registered for a visit to {COMPANY_NAME}.

📋 Registration Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Registration ID: {appointment_id}
• Name: {visitor_data['name']}
• Email: {visitor_data['email']}
• Phone: {visitor_data['phone']}
• Company: {visitor_data.get('company_name', 'N/A')}{company_text}
• Vehicle: {visitor_data.get('vehicle_number', 'N/A')}
• Purpose: {visitor_data['purpose']}{meeting_text}
• Date & Time: {visitor_data['appointment_date']}
{f'• Notes: {visitor_data["notes"]}' if visitor_data.get('notes') else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Status: PENDING APPROVAL

🔗 Action Required:
Please log in to the Admin Portal to review and approve/reject this request.

Admin Portal: /admin/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
        for email in admin_emails:
            send_email(email, admin_subject, admin_body)
        print(f"✅ Registration notification sent to {len(admin_emails)} admin/manager recipients")

    purpose = visitor_data.get('purpose', '')
    meeting_person_email = None
    meeting_person_name = None
    meeting_with = visitor_data.get('meeting_with', '')

    if purpose == 'Data Center':
        if 'Mr. Abhinav Kotagiri' in meeting_with:
            meeting_person_email = 'mannamvenkatadinesh@gmail.com'
            meeting_person_name = 'Mr. Abhinav Kotagiri'
            print(f"📧 Data Center - Will notify: {meeting_person_name} ({meeting_person_email})")
    elif purpose == 'Maintenance':
        maintenance_type = visitor_data.get('maintenance_type', '')
        if maintenance_type == 'IT':
            meeting_person_email = PURPOSE_MEETING_DETAILS['Maintenance']['IT']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Maintenance']['IT']['person_name']
        elif maintenance_type == 'Non IT':
            meeting_person_email = PURPOSE_MEETING_DETAILS['Maintenance']['Non IT']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Maintenance']['Non IT']['person_name']
    elif purpose == 'Meeting':
        meeting_person_email, meeting_person_name = get_meeting_person_details(meeting_with)

    if meeting_person_email:
        meeting_subject = f"📅 New Visitor Registration - {visitor_data['name']} wants to meet you"
        meeting_body = f"""
NEW VISITOR REGISTRATION ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A visitor has registered to meet with you at {COMPANY_NAME}.

📋 Visitor Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {visitor_data['name']}
• Email: {visitor_data['email']}
• Phone: {visitor_data['phone']}
• Company: {visitor_data.get('company_name', 'N/A')}{company_text}
• Purpose: {visitor_data['purpose']}{meeting_text}
• Date & Time: {visitor_data['appointment_date']}
{f'• Notes: {visitor_data["notes"]}' if visitor_data.get('notes') else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Status: PENDING APPROVAL (Waiting for admin approval)

You will be notified once the visit is approved.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
        send_email(meeting_person_email, meeting_subject, meeting_body)
        print(f"✅ Notification sent to meeting person: {meeting_person_name} ({meeting_person_email})")

    return True

def send_thankyou_email(to_email, name, appointment_date, purpose, meeting_with, appointment_id):
    meeting_text = f"\n- Meeting With: {meeting_with}" if meeting_with else ''

    subject = f"Thank You for Registering with {COMPANY_NAME}"
    body = f"""
Dear {name},

Thank you for registering your visit to {COMPANY_NAME}.

We have received your registration request and it is currently pending approval.

📋 Registration Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Registration ID: {appointment_id}
• Name: {name}
• Email: {to_email}
• Purpose: {purpose}{meeting_text}
• Date & Time: {appointment_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Status: PENDING APPROVAL

What happens next?
1. Our team will review your registration
2. You will receive an approval email once confirmed
3. Please bring a valid government-issued ID on the day of your visit

Thank you for choosing {COMPANY_NAME}.

Best regards,
{COMPANY_NAME} Management
"""
    send_email(to_email, subject, body)

VISITOR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visitor Pre-Registration - PI Data Centers</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        input, select, textarea { width: 100%; padding: 12px; margin: 8px 0 15px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        button { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; width: 100%; }
        button:disabled { background: #cccccc; cursor: not-allowed; }
        .meeting-field { display: none; margin-top: 5px; }
        .meeting-field.show { display: block; }
        .maintenance-subtype { display: none; margin-top: 5px; }
        .maintenance-subtype.show { display: block; }
        .data-center-subtype { display: none; margin-top: 5px; }
        .data-center-subtype.show { display: block; }
        .authorised-person-field { display: none; margin-top: 5px; }
        .authorised-person-field.show { display: block; }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 15px; display: none; position: fixed; top: 20px; right: 20px; z-index: 1000; min-width: 300px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .alert-success { background: #d4edda; color: #155724; display: block; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; border: 1px solid #f5c6cb; }
        .status-card { background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px; }
        .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
        .badge.pending { background: #ff9800; color: white; }
        .badge.approved { background: #4caf50; color: white; }
        .badge.rejected { background: #f44336; color: white; }
        .back-link { text-align: center; margin-top: 20px; }
        .back-link a { color: white; text-decoration: none; }
        .logo-container { text-align: center; margin-bottom: 20px; }
        .logo-img { width: 80px; height: 80px; object-fit: contain; margin-bottom: 10px; }
        .page-title { color: #1e3c72; font-size: 24px; margin-top: 10px; }
        .page-subtitle { color: #666; font-size: 14px; }
        .info-box { background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 15px; font-size: 13px; color: #1976d2; }
        .info-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .visitor-names-section { background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; }
        .visitor-entry { background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #e0e0e0; position: relative; }
        .visitor-entry input { margin-bottom: 8px; }
        .visitor-entry input:last-child { margin-bottom: 0; }
        .remove-visitor { position: absolute; top: 10px; right: 10px; background: #f44336; color: white; border: none; border-radius: 50%; width: 25px; height: 25px; cursor: pointer; font-size: 14px; }
        .add-visitor-btn { background: #4caf50; margin-top: 10px; width: auto; padding: 8px 16px; }
        .visitor-count { font-size: 14px; color: #666; margin-bottom: 10px; }
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
                ℹ️ After submission, you will receive a confirmation email.
            </div>

            <div id="alert" class="alert"></div>

            <form id="registerForm" onsubmit="return submitRegistration()">
                <input type="text" id="company" placeholder="Company Name">
                <input type="text" id="vehicle" placeholder="Vehicle Number">
                <select id="purpose" required onchange="handlePurposeChange()">
                    <option value="">Select Purpose *</option>
                    <option value="Data Center">Data Center</option>
                    <option value="Meeting">Meeting</option>
                    <option value="Maintenance">Maintenance</option>
                </select>
                <div id="dataCenterSubtype" class="data-center-subtype">
                    <label>🏢 Data Center Type *</label>
                    <select id="dataCenterType" onchange="updateDataCenterMeetingWith()">
                        <option value="">Select Type *</option>
                        <option value="Tour">Tour</option>
                        <option value="Visit">Visit</option>
                    </select>
                    <div id="authorisedPersonField" class="authorised-person-field">
                        <label>👤 Authorised Person *</label>
                        <select id="authorisedPerson" onchange="updateAuthorisedPerson()">
                            <option value="Mr. Abhinav Kotagiri">Mr. Abhinav Kotagiri</option>
                        </select>
                    </div>
                    <div class="info-text" id="dataCenterInfo"></div>
                </div>
                <div id="meetingField" class="meeting-field">
                    <label>👤 Meeting With *</label>
                    <select id="meetingWith">
                        <option value="">Select Person *</option>
                        <option value="Mr.Kalyan Muppaneni">Mr.Kalyan Muppaneni</option>
                        <option value="Ms.Swapna Lopelly">Ms.Swapna Lopelly </option>
                        <option value="Mr.Abhinav Kotagiri">Mr.Abhinav Kotagiri</option>
                        <option value="Mr.KVS Prakasa Rao">Mr.KVS Prakasa Rao</option>
                        <option value="Mr.Manoj Muppaneni">Mr.Manoj Muppaneni</option>
                        <option value="Mr.Haneesh Kumar">Mr.Haneesh Kumar</option>
                        <option value="Mr.Sreekanth Vatipally">Mr.Sreekanth Vatipally</option>
                    </select>
                </div>
                <div id="maintenanceSubtype" class="maintenance-subtype">
                    <label>🔧 Maintenance Type *</label>
                    <select id="maintenanceType" onchange="updateMaintenanceMeetingWith()">
                        <option value="">Select Type</option>
                        <option value="IT">IT </option>
                        <option value="Non IT">Non IT</option>
                    </select>
                    <div class="info-text" id="maintenanceInfo"></div>
                </div>

                <div class="visitor-names-section">
                    <label>👥 Visitor Details *</label>
                    <div class="visitor-count" id="visitorCount">Visitors: 1</div>
                    <div id="visitorsContainer">
                        <div class="visitor-entry">
                            <input type="text" class="visitor-name" placeholder="Visitor Name *" required>
                            <input type="email" class="visitor-email" placeholder="Visitor Email *" required>
                            <input type="tel" class="visitor-phone" placeholder="Visitor Phone *" required>
                        </div>
                    </div>
                    <button type="button" class="add-visitor-btn" onclick="addVisitor()">+ Add Another Visitor</button>
                </div>

                <label>Appointment Date & Time *</label>
                <input type="datetime-local" id="appointmentDate" required>
                <textarea id="notes" rows="3" placeholder="Additional Notes (Optional)"></textarea>
                <button type="submit">📤 Submit Registration</button>
            </form>
        </div>

        <div class="card">
            <h2 style="color: #1e3c72; margin-bottom: 20px; text-align: center;">🔍 Check Registration Status</h2>
            <input type="email" id="checkEmail" placeholder="Enter your email">
            <button onclick="checkStatus()">Check Status</button>
            <div id="statusResult" class="status-card" style="display:none;"></div>
        </div>

        <div class="back-link">
            <a href="/" style="color: #1e3c72;">← Back to Gateway</a>
        </div>
    </div>

    <script>
        let visitorCount = 1;

        function addVisitor() {
            visitorCount++;
            const container = document.getElementById('visitorsContainer');
            const newEntry = document.createElement('div');
            newEntry.className = 'visitor-entry';
            newEntry.innerHTML = `
                <input type="text" class="visitor-name" placeholder="Visitor Name *" required>
                <input type="email" class="visitor-email" placeholder="Visitor Email *" required>
                <input type="tel" class="visitor-phone" placeholder="Visitor Phone *" required>
                <button type="button" class="remove-visitor" onclick="removeVisitor(this)">×</button>
            `;
            container.appendChild(newEntry);
            document.getElementById('visitorCount').textContent = `Visitors: ${visitorCount}`;
        }

        function removeVisitor(btn) {
            if (visitorCount > 1) {
                btn.parentElement.remove();
                visitorCount--;
                document.getElementById('visitorCount').textContent = `Visitors: ${visitorCount}`;
            }
        }

        function getVisitorList() {
            const nameInputs = document.querySelectorAll('.visitor-name');
            const emailInputs = document.querySelectorAll('.visitor-email');
            const phoneInputs = document.querySelectorAll('.visitor-phone');
            const visitors = [];
            for (let i = 0; i < nameInputs.length; i++) {
                const name = nameInputs[i].value.trim();
                const email = emailInputs[i].value.trim();
                const phone = phoneInputs[i].value.trim();
                if (name && email && phone) {
                    visitors.push({ name: name, email: email, phone: phone });
                }
            }
            return visitors;
        }

        function handlePurposeChange() {
            const purpose = document.getElementById('purpose').value;
            const meetingField = document.getElementById('meetingField');
            const maintenanceSubtype = document.getElementById('maintenanceSubtype');
            const dataCenterSubtype = document.getElementById('dataCenterSubtype');
            const authorisedPersonField = document.getElementById('authorisedPersonField');
            const meetingWithInput = document.getElementById('meetingWith');

            meetingField.classList.remove('show');
            maintenanceSubtype.classList.remove('show');
            dataCenterSubtype.classList.remove('show');
            authorisedPersonField.classList.remove('show');

            if (purpose === 'Meeting') {
                meetingField.classList.add('show');
                meetingWithInput.value = '';
                meetingWithInput.required = true;
                meetingWithInput.disabled = false;
            } else if (purpose === 'Data Center') {
                dataCenterSubtype.classList.add('show');
                document.getElementById('dataCenterType').value = '';
                meetingWithInput.value = '';
                meetingWithInput.required = false;
                meetingWithInput.disabled = true;
                document.getElementById('dataCenterInfo').innerHTML = '';
                authorisedPersonField.classList.remove('show');
            } else if (purpose === 'Maintenance') {
                maintenanceSubtype.classList.add('show');
                meetingWithInput.value = '';
                meetingWithInput.required = false;
                meetingWithInput.disabled = false;
                document.getElementById('maintenanceType').value = '';
                document.getElementById('maintenanceInfo').innerHTML = '';
            } else {
                meetingWithInput.value = '';
                meetingWithInput.required = false;
                meetingWithInput.disabled = false;
            }
        }

        function updateDataCenterMeetingWith() {
            const dataCenterType = document.getElementById('dataCenterType').value;
            const meetingWithInput = document.getElementById('meetingWith');
            const authorisedPersonField = document.getElementById('authorisedPersonField');
            const infoDiv = document.getElementById('dataCenterInfo');
            
            if (dataCenterType === 'Tour') {
                authorisedPersonField.classList.add('show');
                const authorisedPerson = document.getElementById('authorisedPerson').value;
                meetingWithInput.value = `${authorisedPerson} - Tour (Data Center)`;
                infoDiv.innerHTML = '<strong>📍 Data Center Tour</strong>';
                meetingWithInput.disabled = true;
            } else if (dataCenterType === 'Visit') {
                authorisedPersonField.classList.add('show');
                const authorisedPerson = document.getElementById('authorisedPerson').value;
                meetingWithInput.value = `${authorisedPerson} - Visit (Data Center)`;
                infoDiv.innerHTML = '<strong>📍 Data Center Visit</strong>';
                meetingWithInput.disabled = true;
            } else {
                authorisedPersonField.classList.remove('show');
                meetingWithInput.value = '';
                infoDiv.innerHTML = '';
                meetingWithInput.disabled = true;
            }
        }

        function updateAuthorisedPerson() {
            const authorisedPerson = document.getElementById('authorisedPerson').value;
            const dataCenterType = document.getElementById('dataCenterType').value;
            const meetingWithInput = document.getElementById('meetingWith');
            
            if (dataCenterType === 'Tour') {
                meetingWithInput.value = `${authorisedPerson} - Tour (Data Center)`;
            } else if (dataCenterType === 'Visit') {
                meetingWithInput.value = `${authorisedPerson} - Visit (Data Center)`;
            }
        }

        function updateMaintenanceMeetingWith() {
            const maintenanceType = document.getElementById('maintenanceType').value;
            const meetingWithInput = document.getElementById('meetingWith');
            const infoDiv = document.getElementById('maintenanceInfo');

            if (maintenanceType === 'IT') {
                meetingWithInput.value = 'Srikanth - IT Department';
                infoDiv.innerHTML = '';
                meetingWithInput.disabled = true;
            } else if (maintenanceType === 'Non IT') {
                meetingWithInput.value = 'Haneesh - Non IT Department';
                infoDiv.innerHTML = '';
                meetingWithInput.disabled = true;
            } else {
                meetingWithInput.value = '';
                infoDiv.innerHTML = '';
                meetingWithInput.disabled = false;
            }
        }

        function showAlert(message, type) {
            const alertDiv = document.getElementById('alert');
            alertDiv.textContent = message;
            alertDiv.className = 'alert alert-' + type;
            alertDiv.style.display = 'block';
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 5000);
        }

        async function submitRegistration() {
            event.preventDefault();

            const company = document.getElementById('company').value.trim();
            const vehicle = document.getElementById('vehicle').value.trim();
            const purpose = document.getElementById('purpose').value;
            let meetingWith = document.getElementById('meetingWith').value.trim();
            const appointmentDate = document.getElementById('appointmentDate').value;
            const notes = document.getElementById('notes').value.trim();
            const maintenanceType = document.getElementById('maintenanceType') ? document.getElementById('maintenanceType').value : '';
            const dataCenterType = document.getElementById('dataCenterType') ? document.getElementById('dataCenterType').value : '';
            const authorisedPerson = document.getElementById('authorisedPerson') ? document.getElementById('authorisedPerson').value : '';
            const visitorList = getVisitorList();

            if (!purpose) { showAlert('Please select a purpose', 'error'); return false; }
            if (visitorList.length === 0) { showAlert('Please add at least one visitor', 'error'); return false; }
            if (!appointmentDate) { showAlert('Please select appointment date and time', 'error'); return false; }

            if (purpose === 'Meeting' && !meetingWith) {
                showAlert('Please select who you are meeting with', 'error');
                return false;
            }
            if (purpose === 'Maintenance' && !maintenanceType) {
                showAlert('Please select maintenance type (IT or Non IT)', 'error');
                return false;
            }
            if (purpose === 'Data Center' && !dataCenterType) {
                showAlert('Please select Data Center type (Tour or Visit)', 'error');
                return false;
            }

            if (purpose === 'Data Center') {
                meetingWith = `${authorisedPerson} - ${dataCenterType} (Data Center)`;
            }
            if (purpose === 'Maintenance') {
                if (maintenanceType === 'IT') {
                    meetingWith = 'Srikanth - IT Department';
                } else if (maintenanceType === 'Non IT') {
                    meetingWith = 'Haneesh - Non IT Department';
                }
            }

            const submitBtn = event.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;

            try {
                let allSuccess = true;
                let errorMessage = '';

                for (const visitor of visitorList) {
                    const response = await fetch('/visitor/api/appointments', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: visitor.name,
                            email: visitor.email,
                            phone: visitor.phone,
                            company_name: company,
                            vehicle_number: vehicle,
                            purpose: purpose,
                            meeting_with: meetingWith,
                            appointment_date: appointmentDate,
                            notes: notes,
                            created_by: 'visitor',
                            maintenance_type: maintenanceType,
                            is_group: visitorList.length > 1 ? 1 : 0,
                            group_members: visitorList.length > 1 ? JSON.stringify(visitorList) : '',
                            data_center_type: dataCenterType
                        })
                    });

                    const resultData = await response.json();

                    if (!response.ok || !resultData.success) {
                        allSuccess = false;
                        errorMessage = resultData?.error || `HTTP ${response.status}`;
                        console.error('API Error:', resultData);
                        break;
                    }
                }

                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

                if (allSuccess) {
                    const msg = visitorList.length === 1
                        ? `✅ Registration submitted successfully for ${visitorList[0].name}! A confirmation email has been sent.`
                        : `✅ Bulk registration submitted successfully for ${visitorList.length} visitors! Each visitor will receive a confirmation email.`;
                    showAlert(msg, 'success');
                    document.getElementById('registerForm').reset();
                    document.getElementById('meetingField').classList.remove('show');
                    document.getElementById('maintenanceSubtype').classList.remove('show');
                    document.getElementById('dataCenterSubtype').classList.remove('show');
                    document.getElementById('authorisedPersonField').classList.remove('show');
                    document.getElementById('visitorsContainer').innerHTML = '<div class="visitor-entry"><input type="text" class="visitor-name" placeholder="Visitor Name *" required><input type="email" class="visitor-email" placeholder="Visitor Email *" required><input type="tel" class="visitor-phone" placeholder="Visitor Phone *" required></div>';
                    visitorCount = 1;
                    document.getElementById('visitorCount').textContent = 'Visitors: 1';
                } else {
                    showAlert('❌ Registration failed: ' + errorMessage, 'error');
                }
            } catch (error) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                showAlert('❌ Registration failed. Please try again.', 'error');
                console.error('Submission error:', error);
            }
            return false;
        }

        async function checkStatus() {
            const email = document.getElementById('checkEmail').value.trim();
            if (!email) { showAlert('Please enter your email', 'error'); return; }

            try {
                const response = await fetch('/visitor/api/appointments/check?email=' + encodeURIComponent(email));
                const registrations = await response.json();
                const resultDiv = document.getElementById('statusResult');

                if (!registrations || registrations.length === 0) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '<p style="color:#666;">No registrations found for this email.</p>';
                    return;
                }

                let html = '<h3 style="margin-bottom:15px;">Your Registrations:</h3>';
                for (const reg of registrations) {
                    let statusBadge = reg.status === 'pending' ? '<span class="badge pending">⏳ PENDING</span>' :
                                    (reg.status === 'approved' ? '<span class="badge approved">✅ APPROVED</span>' :
                                    '<span class="badge rejected">❌ REJECTED</span>');

                    let groupInfo = '';
                    if (reg.is_group && reg.group_members) {
                        try {
                            const members = JSON.parse(reg.group_members);
                            groupInfo = '<p><strong>👥 Group Registration:</strong> Part of a group of ' + members.length + ' visitors</p>';
                        } catch(e) {}
                    }

                    let dataCenterInfo = '';
                    if (reg.purpose === 'Data Center' && reg.data_center_type) {
                        dataCenterInfo = `<p><strong>🏢 Data Center Type:</strong> ${escapeHtml(reg.data_center_type)}</p>`;
                    }

                    html += `<div style="border-top:1px solid #ddd; padding:10px 0;">
                        <p><strong>📅 Date:</strong> ${new Date(reg.appointment_date).toLocaleString()}</p>
                        <p><strong>👤 Name:</strong> ${escapeHtml(reg.name)}</p>
                        <p><strong>📧 Email:</strong> ${escapeHtml(reg.email)}</p>
                        <p><strong>📞 Phone:</strong> ${escapeHtml(reg.phone)}</p>
                        <p><strong>🏢 Company:</strong> ${escapeHtml(reg.company_name || 'N/A')}</p>
                        <p><strong>📝 Purpose:</strong> ${escapeHtml(reg.purpose)}</p>
                        ${dataCenterInfo}
                        <p><strong>👤 Meeting With:</strong> ${escapeHtml(reg.meeting_with || 'N/A')}</p>
                        ${groupInfo}
                        <p><strong>📊 Status:</strong> ${statusBadge}</p>
                        ${reg.rejection_reason ? '<p><strong>❌ Reason:</strong> ' + escapeHtml(reg.rejection_reason) + '</p>' : ''}
                    </div>`;
                }
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = html;
            } catch (error) {
                showAlert('Error checking status. Please try again.', 'error');
                console.error('Status check error:', error);
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

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
            cursor.execute("SHOW COLUMNS FROM appointments")
            columns = [col[0] for col in cursor.fetchall()]

            insert_fields = ['appointment_id', 'name', 'email', 'phone', 'company_name', 'vehicle_number', 'purpose', 'meeting_with', 'appointment_date', 'notes', 'status', 'created_by', 'maintenance_type']
            insert_values = [appointment_id, data['name'], data['email'], data['phone'], data.get('company_name',''), data.get('vehicle_number',''),
                           data['purpose'], data.get('meeting_with',''), data['appointment_date'], data.get('notes',''),
                           'pending', data.get('created_by','visitor'), data.get('maintenance_type','')]

            if 'is_group' in columns:
                insert_fields.append('is_group')
                insert_values.append(data.get('is_group', 0))
            if 'group_members' in columns:
                insert_fields.append('group_members')
                insert_values.append(data.get('group_members', ''))
            if 'data_center_type' in columns:
                insert_fields.append('data_center_type')
                insert_values.append(data.get('data_center_type', ''))

            placeholders = ','.join(['%s'] * len(insert_fields))
            query = f"INSERT INTO appointments ({','.join(insert_fields)}) VALUES ({placeholders})"
            cursor.execute(query, insert_values)
            conn.commit()
            cursor.close()
            conn.close()

            print(f"✅ Appointment added: {appointment_id} for {data['name']}")

            send_thankyou_email(data['email'], data['name'], data['appointment_date'], data['purpose'], data.get('meeting_with', ''), appointment_id)

            visitor_data = {
                'name': data['name'], 'email': data['email'], 'phone': data['phone'],
                'company_name': data.get('company_name', ''), 'vehicle_number': data.get('vehicle_number', ''),
                'purpose': data['purpose'], 'meeting_with': data.get('meeting_with', ''),
                'appointment_date': data['appointment_date'], 'notes': data.get('notes', ''),
                'maintenance_type': data.get('maintenance_type', ''),
                'data_center_type': data.get('data_center_type', '')
            }
            send_registration_notification(visitor_data, appointment_id)

            return jsonify({'success': True, 'appointment_id': appointment_id})
        except Exception as e:
            print(f"Error adding appointment: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Failed'}), 500

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
    print("   Access via: http://visitor.picloud.in/visitor/")
    print("=" * 60)
    app.run(host='127.0.0.1', port=8083, debug=False)
