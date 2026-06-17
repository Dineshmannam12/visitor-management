from flask import Flask, request, jsonify, render_template_string, session, send_file
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import get_logo_base64, COMPANY_NAME, EMAIL_CONFIG
import io
import base64
import os
import tempfile
import traceback
import re
from PIL import Image as PILImage

# PDF libraries
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"ReportLab not available: {e}")
    REPORTLAB_AVAILABLE = False

COMPACT_PAGE_SIZE = (210*mm, 148*mm)

app = Flask(__name__)
app.secret_key = 'security_secret_key_2024'
CORS(app)

# Background image path
BACKGROUND_PATH = 'static/securityimage.jpg'

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

@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

def send_email(to_email, subject, body, attachment=None, attachment_filename=None):
    if not to_email or to_email == 'string' or '@' not in to_email:
        print(f"⚠️ Invalid email address: {to_email}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
            msg.attach(part)

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

def save_base64_image_temp(photo_base64):
    if not photo_base64:
        return None

    try:
        if ',' in photo_base64:
            img_data = photo_base64.split(',')[1]
        else:
            img_data = photo_base64

        img_data = re.sub(r'\s+', '', img_data)
        image_bytes = base64.b64decode(img_data)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(image_bytes)
        temp_file.close()

        try:
            with PILImage.open(temp_file.name) as img:
                img.verify()
            print(f"✅ Valid image saved to {temp_file.name}")
            return temp_file.name
        except Exception as e:
            print(f"Invalid image file: {e}")
            os.unlink(temp_file.name)
            return None

    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return None

def generate_visitor_pdf(visitor_data, visitor_id, photo_base64=None):
    if not REPORTLAB_AVAILABLE:
        print("ReportLab not available, skipping PDF generation")
        return None

    temp_image_path = None
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=COMPACT_PAGE_SIZE,
                                topMargin=0.2*inch, bottomMargin=0.2*inch,
                                leftMargin=0.2*inch, rightMargin=0.2*inch)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14,
                                      textColor=colors.HexColor('#1e3c72'), alignment=TA_CENTER, spaceAfter=8)
        elements.append(Paragraph("PI DATA CENTERS", title_style))

        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=10,
                                         textColor=colors.HexColor('#2a5298'), alignment=TA_CENTER, spaceAfter=5)
        elements.append(Paragraph("VISITOR BADGE", subtitle_style))

        checkin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER)
        elements.append(Paragraph(f"Issued: {checkin_time}", date_style))
        elements.append(Spacer(1, 0.1*inch))

        visitor_info = [
            ['Name', visitor_data.get('name', 'N/A')],
            ['Company', visitor_data.get('company_name', 'N/A')],
            ['Purpose', visitor_data.get('purpose', 'N/A')],
        ]

        if visitor_data.get('meeting_with'):
            visitor_info.append(['Meeting', visitor_data.get('meeting_with', 'N/A')])

        visitor_info.append(['Vehicle', visitor_data.get('vehicle_number', 'N/A')])
        visitor_info.append(['Badge ID', visitor_id])

        table = Table(visitor_info, colWidths=[0.9*inch, 2.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.1*inch))

        if photo_base64:
            print("Processing photo for PDF...")
            temp_image_path = save_base64_image_temp(photo_base64)

            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    img = Image(temp_image_path, width=1.5*inch, height=1.5*inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.05*inch))
                    print("✅ Photo added to PDF successfully")
                except Exception as img_error:
                    print(f"Error adding image to PDF: {img_error}")
                    elements.append(Paragraph("No photo", styles['Normal']))
            else:
                print("Could not save image to temp file")
                elements.append(Paragraph("No photo", styles['Normal']))
        else:
            print("No photo provided for PDF")
            elements.append(Paragraph("No photo", styles['Normal']))

        elements.append(Spacer(1, 0.05*inch))
        instr_style = ParagraphStyle('Instructions', parent=styles['Normal'], fontSize=6, alignment=TA_CENTER)
        instructions = [
            "Valid for current visit only",
            "Display badge at all times"
        ]
        for instr in instructions:
            elements.append(Paragraph(instr, instr_style))

        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=5, alignment=TA_CENTER, textColor=colors.HexColor('#999999'))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("PI DATA CENTERS - VMS", footer_style))

        doc.build(elements)
        buffer.seek(0)
        print("✅ Compact PDF generated successfully")
        return buffer

    except Exception as e:
        print(f"PDF generation error: {e}")
        traceback.print_exc()
        return None
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
                print(f"Cleaned up temp file: {temp_image_path}")
            except:
                pass

def send_checkin_notifications(visitor_data, visitor_id, pdf_buffer=None):
    meeting_text = f"\n- Meeting With: {visitor_data.get('meeting_with', 'N/A')}" if visitor_data.get('meeting_with') else ''
    company_text = f"\n- Company: {visitor_data.get('company_name', 'N/A')}" if visitor_data.get('company_name') else ''
    checkin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    meeting_person_email = None
    meeting_person_name = None
    purpose = visitor_data.get('purpose', '')
    meeting_with = visitor_data.get('meeting_with', '')

    if purpose == 'Data Center':
        data_center_type = visitor_data.get('data_center_type', '')
        if data_center_type == 'Tour':
            meeting_person_email = PURPOSE_MEETING_DETAILS['Data Center']['Tour']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Data Center']['Tour']['person_name']
        elif data_center_type == 'Visit':
            meeting_person_email = PURPOSE_MEETING_DETAILS['Data Center']['Visit']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Data Center']['Visit']['person_name']
        print(f"📧 Data Center ({data_center_type}) - Will notify: {meeting_person_name} ({meeting_person_email})")
    elif purpose == 'Maintenance':
        if 'IT' in meeting_with or 'Srikanth' in meeting_with:
            meeting_person_email = PURPOSE_MEETING_DETAILS['Maintenance']['IT']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Maintenance']['IT']['person_name']
            print(f"📧 Maintenance (IT) - Will notify: {meeting_person_name} ({meeting_person_email})")
        else:
            meeting_person_email = PURPOSE_MEETING_DETAILS['Maintenance']['Non IT']['email']
            meeting_person_name = PURPOSE_MEETING_DETAILS['Maintenance']['Non IT']['person_name']
            print(f"📧 Maintenance (Non IT) - Will notify: {meeting_person_name} ({meeting_person_email})")
    elif purpose == 'Meeting':
        meeting_person_email, meeting_person_name = get_meeting_person_details(meeting_with)
        if meeting_person_email:
            print(f"📧 Meeting - Will notify: {meeting_person_name} ({meeting_person_email})")
        else:
            print(f"⚠️ Meeting - No specific person found for: {meeting_with}")

    visitor_subject = f"✅ Check-in Confirmation - {COMPANY_NAME}"
    visitor_body = f"""
Dear {visitor_data['name']},

You have been successfully checked in to {COMPANY_NAME}.

📋 Check-in Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {visitor_data['name']}
• Email: {visitor_data['email']}
• Phone: {visitor_data['phone']}
• Company: {visitor_data.get('company_name', 'N/A')}{company_text}
• Vehicle: {visitor_data.get('vehicle_number', 'N/A')}
• Purpose: {visitor_data['purpose']}{meeting_text}
• Check-in Time: {checkin_time}
• Badge ID: {visitor_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: CHECKED IN

Please find attached your compact visitor badge PDF.

Important Information:
- Please display your visitor badge at all times
- Report to security desk when you are ready to check out

Thank you for visiting {COMPANY_NAME}.

Best regards,
{COMPANY_NAME} Security Team
"""

    if pdf_buffer:
        pdf_content = pdf_buffer.getvalue()
        send_email(visitor_data['email'], visitor_subject, visitor_body, pdf_content, f"visitor_badge_{visitor_id}.pdf")
        print(f"✅ Email with PDF sent to visitor: {visitor_data['email']}")
    else:
        send_email(visitor_data['email'], visitor_subject, visitor_body)
        print(f"⚠️ No PDF generated, email sent without attachment to {visitor_data['email']}")

    if meeting_person_email:
        meeting_subject = f"🔔 Visitor Check-in Notification - {visitor_data['name']}"
        meeting_body = f"""
VISITOR CHECK-IN NOTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A visitor has been checked in to meet with you.

📋 Visitor Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {visitor_data['name']}
• Email: {visitor_data['email']}
• Phone: {visitor_data['phone']}
• Company: {visitor_data.get('company_name', 'N/A')}
• Vehicle: {visitor_data.get('vehicle_number', 'N/A')}
• Purpose: {visitor_data['purpose']}
• Meeting With: {visitor_data.get('meeting_with', 'N/A')}
• Check-in Time: {checkin_time}
• Badge ID: {visitor_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: CHECKED IN (Currently Inside Facility)

Please ensure you are available to meet them.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
        send_email(meeting_person_email, meeting_subject, meeting_body)
        print(f"✅ Notification sent to meeting person: {meeting_person_name} ({meeting_person_email})")

    staff_emails = get_all_notification_emails()
    if staff_emails:
        staff_subject = f"🔔 VISITOR CHECK-IN ALERT - {visitor_data['name']}"
        staff_body = f"""
VISITOR CHECK-IN NOTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A visitor has been checked in to the facility.

📋 Visitor Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Name: {visitor_data['name']}
• Email: {visitor_data['email']}
• Phone: {visitor_data['phone']}
• Company: {visitor_data.get('company_name', 'N/A')}
• Vehicle: {visitor_data.get('vehicle_number', 'N/A')}
• Purpose: {visitor_data['purpose']}{meeting_text}
• Check-in Time: {checkin_time}
• Badge ID: {visitor_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: CHECKED IN (Currently Inside Facility)

{f'A notification has been sent to {meeting_person_name} ({meeting_person_email})' if meeting_person_email else 'No meeting person notification was sent for this visit.'}

A compact PDF badge has been sent to the visitor's email.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} Visitor Management System
"""
        for email in staff_emails:
            send_email(email, staff_subject, staff_body)
        print(f"✅ Notifications sent to {len(staff_emails)} staff recipients")
    else:
        print("⚠️ No staff emails configured. Please set up email settings in Admin Portal.")

    return True

SECURITY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Service - PI Data Centers</title>
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
        input, select, textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.9);
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
            background: white;
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
            transition: all 0.3s ease;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        button:disabled {
            background: #cccccc;
            cursor: not-allowed;
            transform: none;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            text-align: center;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        .stat-card h3 { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .stat-card p { font-size: 32px; font-weight: bold; color: #1e3c72; }
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
        .tab-btn.active { background: #1e3c72; color: white; }
        .tab-btn.highlight-active {
            background: linear-gradient(135deg, #2196F3, #1976D2);
            color: white;
            animation: pulseBlue 2s infinite;
        }
        .tab-btn.highlight-approved {
            background: linear-gradient(135deg, #4caf50, #388e3c);
            color: white;
        }
        .tab-btn.highlight-active.active, .tab-btn.highlight-approved.active {
            background: #1e3c72;
            color: white;
        }
        @keyframes pulseBlue {
            0% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(33, 150, 243, 0); }
            100% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0); }
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
        .tab-count.hidden { display: none; }
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
            border-left: 4px solid #1e3c72;
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
        .badge.in { background: linear-gradient(135deg, #2196F3, #1976D2); color: white; }
        .badge.out { background: linear-gradient(135deg, #9e9e9e, #757575); color: white; }
        .badge.approved { background: linear-gradient(135deg, #4caf50, #388e3c); color: white; }
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
        .btn-checkout { background: linear-gradient(135deg, #4caf50, #388e3c); }
        .btn-pdf { background: linear-gradient(135deg, #ff9800, #f57c00); }
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
        .photo-preview .placeholder { color: #999; text-align: center; }
        .camera-btn { background: #2196F3; width: auto; margin: 5px; padding: 10px 20px; }
        .meeting-field { display: none; margin-top: 5px; }
        .meeting-field.show { display: block; }
        .maintenance-subtype { display: none; margin-top: 5px; }
        .maintenance-subtype.show { display: block; }
        .data-center-subtype { display: none; margin-top: 5px; }
        .data-center-subtype.show { display: block; }
        .authorised-person-field { display: none; margin-top: 5px; }
        .authorised-person-field.show { display: block; }
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
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 15px; display: none; position: fixed; top: 20px; right: 20px; z-index: 1000; min-width: 300px; animation: slideInRight 0.3s ease; }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .alert-success { background: #d4edda; color: #155724; display: block; border-left: 4px solid #28a745; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; border-left: 4px solid #dc3545; }
        .alert-info { background: #d1ecf1; color: #0c5460; display: block; border-left: 4px solid #17a2b8; }
        .grid { display: grid; gap: 20px; grid-template-columns: 1fr 1fr; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .button-group { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
        .logo-container { text-align: center; margin-bottom: 20px; }
        .logo-img { width: 80px; height: 80px; object-fit: contain; margin-bottom: 10px; }
        .login-title { color: #1e3c72; font-size: 24px; margin-top: 10px; }
        .login-subtitle { color: #666; font-size: 14px; }
        .info-text { font-size: 12px; color: #666; margin-top: 5px; }
        .info-text strong { color: #1e3c72; }
        .info-text span { color: #2a5298; font-weight: 600; }
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .loading-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            min-width: 300px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1e3c72;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .empty-state { text-align: center; padding: 40px; color: #999; }
        .empty-state-icon { font-size: 48px; margin-bottom: 10px; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #1e3c72, #2a5298); border-radius: 10px; }

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
    <div id="loadingOverlay" class="loading-overlay">
        <div class="loading-content">
            <div class="spinner"></div>
            <div class="loading-text">Processing Check-in...</div>
            <div class="loading-subtext">Please wait while we complete the check-in process</div>
        </div>
    </div>

    <div id="loginPage">
        <div class="container">
            <div class="login-wrapper">
                <div class="login-card">
                    <div class="login-left">
                        <div class="login-brand">
                            <h1>Security Portal</h1>
                            <p>Pi Datacenters Security</p>
                        </div>
                        <div class="login-features">
                            <div class="feature-item">
                                <span class="feature-icon">✅</span>
                                <span>Visitor Check-in</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">🚪</span>
                                <span>Visitor Check-out</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">📊</span>
                                <span>View Reports</span>
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
                            <p>Sign in to your security account</p>
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
                🔒 Pi Datacenters <span>Security Portal</span>
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
            <h1 style="color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.3); font-size: 28px; margin-bottom: 5px;">Pi Datacenters Security Service</h1>
            <div style="color: rgba(255,255,255,0.85); text-align: center; margin-bottom: 20px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); font-size: 16px;">Check-in / Check-out Management</div>

            <div class="tabs">
                <button class="tab-btn active" id="checkinTabBtn" onclick="showTab('checkin')">
                    ✅ Check In
                </button>
                <button class="tab-btn" id="activeTabBtn" onclick="showTab('active')">
                    🏢 Active Visitors
                    <span id="activeCount" class="tab-count">0</span>
                </button>
                <button class="tab-btn" id="approvedTabBtn" onclick="showTab('approved')">
                    📋 Approved Appointments
                    <span id="approvedTabCount" class="tab-count">0</span>
                </button>
            </div>

            <div id="checkinTab" class="tab-content active">
                <div class="grid">
                    <div class="card">
                        <h2>Check In Visitor</h2>
                        <form id="checkinForm" onsubmit="return submitCheckin()">
                            <input type="text" id="name" placeholder="Full Name *" required>
                            <input type="email" id="email" placeholder="Email *" required>
                            <input type="tel" id="phone" placeholder="Phone *" required>
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
                                    <option value="Ms.Swapna Lopelly">Ms.Swapna Lopelly</option>
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
                                    <option value="IT">IT</option>
                                    <option value="Non IT">Non IT</option>
                                </select>
                                <div class="info-text" id="maintenanceInfo"></div>
                            </div>
                            <div class="photo-container">
                                <label>📸 Visitor Photo *</label>
                                <div class="photo-preview" id="photoPreview">
                                    <div class="placeholder">No photo uploaded</div>
                                </div>
                                <input type="hidden" id="visitorPhoto">
                                <div class="button-group">
                                    <button type="button" class="camera-btn" onclick="uploadPhoto()">📁 Upload Photo</button>
                                </div>
                            </div>
                            <button type="submit" id="checkinBtn">✅ Check In Visitor</button>
                        </form>
                    </div>
                    <div class="card">
                        <h2>📊 Quick Stats</h2>
                        <div class="stats">
                            <div class="stat-card">
                                <h3>🏢 Inside Now</h3>
                                <p id="insideStat">0</p>
                            </div>
                            <div class="stat-card">
                                <h3>✅ Today's Check-ins</h3>
                                <p id="todayStat">0</p>
                            </div>
                            <div class="stat-card">
                                <h3>🚪 Today's Check-outs</h3>
                                <p id="checkedOutStat">0</p>
                            </div>
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
        let autoRefreshInterval = null;

        function getBasePath() {
            const pathname = window.location.pathname;
            if (pathname.startsWith('/security/')) {
                return '/security';
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

        function highlightTab(tabId, hasItems, type) {
            const tabBtn = document.getElementById(tabId);
            if (!tabBtn) return;
            tabBtn.classList.remove('highlight-active', 'highlight-approved');
            if (hasItems) {
                if (type === 'active') {
                    tabBtn.classList.add('highlight-active');
                } else if (type === 'approved') {
                    tabBtn.classList.add('highlight-approved');
                }
            }
        }

        function showLoadingOverlay() {
            document.getElementById('loadingOverlay').style.display = 'flex';
        }

        function hideLoadingOverlay() {
            document.getElementById('loadingOverlay').style.display = 'none';
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
            if (result && result.success) {
                currentUser = result.username;
                sessionStorage.setItem('security_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadAllData();
                if (autoRefreshInterval) clearInterval(autoRefreshInterval);
                autoRefreshInterval = setInterval(loadAllData, 30000);
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
            sessionStorage.removeItem('security_user');
            
            // Clear auto refresh interval
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
            
            // Show login page, hide main app
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
            
            // Clear any pending appointment
            window.pendingAppointmentId = null;
            
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
            let tabIndex = { checkin: 0, active: 1, approved: 2 }[tab];
            if (tabButtons[tabIndex]) {
                tabButtons[tabIndex].classList.add('active');
            }
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
                document.getElementById('insideStat').textContent = stats.inside || 0;
                document.getElementById('todayStat').textContent = stats.today || 0;
                document.getElementById('checkedOutStat').textContent = stats.checkedOutToday || 0;
            }
        }

        function getEmptyStateMessage(type) {
            const messages = {
                active: { icon: '🏢', text: 'No visitors currently inside' },
                approved: { icon: '✅', text: 'No approved appointments available' }
            };
            const msg = messages[type] || { icon: '📋', text: 'No records found' };
            return `<div class="empty-state">
                        <div class="empty-state-icon">${msg.icon}</div>
                        <div>${msg.text}</div>
                    </div>`;
        }

        async function loadActiveVisitors() {
            const visitors = await api('/api/visitors?status=in');
            const container = document.getElementById('activeList');
            const activeCount = visitors ? visitors.length : 0;
            updateCountBadge('activeCount', activeCount);
            highlightTab('activeTabBtn', activeCount > 0, 'active');
            if (!visitors || visitors.length === 0) {
                container.innerHTML = getEmptyStateMessage('active');
                return;
            }
            container.innerHTML = visitors.map(v => `
                <div class="visitor-item">
                    <strong>${escapeHtml(v.name)}</strong><br>
                    📧 ${escapeHtml(v.email)} | 📞 ${escapeHtml(v.phone)}<br>
                    🏢 ${escapeHtml(v.company_name || 'N/A')}<br>
                    🚗 ${escapeHtml(v.vehicle_number || 'N/A')} | 📝 ${escapeHtml(v.purpose)}<br>
                    ${v.meeting_with ? '👤 Meeting: ' + escapeHtml(v.meeting_with) + '<br>' : ''}
                    🕐 ${v.check_in_time}<br>
                    ${v.photo ? '<img src="' + v.photo + '" style="width:50px;height:50px;border-radius:50%;margin-top:5px;">' : ''}<br>
                    <span class="badge in">INSIDE</span><br>
                    <div class="button-group">
                        <button class="btn-small btn-checkout" onclick="checkoutVisitor('${v.visitor_id || v.id}')">🚪 Check Out</button>
                        <button class="btn-small btn-pdf" onclick="downloadPDF('${v.visitor_id || v.id}')">📄 Download PDF</button>
                    </div>
                </div>
            `).join('');
        }

        async function loadApprovedAppointments() {
            const regularApps = await api('/api/appointments?status=approved');
            const container = document.getElementById('approvedList');
            let allApps = [];
            if (regularApps && regularApps.length > 0) {
                allApps = allApps.concat(regularApps);
            }
            const approvedCount = allApps.length;
            updateCountBadge('approvedTabCount', approvedCount);
            highlightTab('approvedTabBtn', approvedCount > 0, 'approved');
            if (!allApps || allApps.length === 0) {
                container.innerHTML = getEmptyStateMessage('approved');
                return;
            }
            container.innerHTML = allApps.map(a => {
                let dataCenterInfo = '';
                if (a.purpose === 'Data Center' && a.data_center_type) {
                    dataCenterInfo = `🏢 Data Center Type: ${escapeHtml(a.data_center_type)}<br>`;
                }
                return `
                    <div class="visitor-item" style="border-left-color: #4caf50;">
                        <strong>${escapeHtml(a.name)}</strong><br>
                        📧 ${escapeHtml(a.email)} | 📞 ${escapeHtml(a.phone)}<br>
                        🏢 ${escapeHtml(a.company_name || 'N/A')}<br>
                        📝 ${escapeHtml(a.purpose)}<br>
                        ${dataCenterInfo}
                        ${a.meeting_with ? '👤 Meeting: ' + escapeHtml(a.meeting_with) + '<br>' : ''}
                        📅 ${new Date(a.appointment_date).toLocaleString()}<br>
                        <span class="badge approved">APPROVED</span><br>
                        <button class="btn-small btn-checkout" onclick="checkInFromAppointment('${a.appointment_id || a.id}')">✅ Check In Now</button>
                    </div>
                `;
            }).join('');
        }

        async function checkInFromAppointment(appointmentId) {
            const appt = await api(`/api/appointments/${appointmentId}`);
            if (appt) {
                // Set basic fields
                document.getElementById('name').value = appt.name;
                document.getElementById('email').value = appt.email;
                document.getElementById('phone').value = appt.phone;
                document.getElementById('company').value = appt.company_name || '';
                document.getElementById('vehicle').value = appt.vehicle_number || '';
                document.getElementById('purpose').value = appt.purpose;
                
                // Store the data center type for later use
                let dataCenterType = appt.data_center_type || '';
                let authorisedPerson = 'Mr. Abhinav Kotagiri';
                
                // If data_center_type is not set, try to extract from meeting_with
                if (!dataCenterType && appt.meeting_with) {
                    const meetingWith = appt.meeting_with;
                    if (meetingWith.includes('Tour')) {
                        dataCenterType = 'Tour';
                    } else if (meetingWith.includes('Visit')) {
                        dataCenterType = 'Visit';
                    }
                    
                    // Extract the person name
                    const nameMatch = meetingWith.match(/^(.*?)\s*-\s*(Tour|Visit)/);
                    if (nameMatch) {
                        authorisedPerson = nameMatch[1].trim();
                    }
                }
                
                // First, trigger purpose change to show/hide appropriate fields
                handlePurposeChange();
                
                // Now set the Data Center fields if applicable
                if (appt.purpose === 'Data Center' && dataCenterType) {
                    // Show the Data Center subtype
                    const dataCenterSubtype = document.getElementById('dataCenterSubtype');
                    dataCenterSubtype.classList.add('show');
                    
                    // Set the Data Center type dropdown
                    const dataCenterTypeSelect = document.getElementById('dataCenterType');
                    dataCenterTypeSelect.value = dataCenterType;
                    
                    // Trigger the change event to show authorised person field
                    dataCenterTypeSelect.dispatchEvent(new Event('change'));
                    // Set the authorised person
                    if (document.getElementById('authorisedPerson')) {
                        const personSelect = document.getElementById('authorisedPerson');
                        // Check if the person exists in the dropdown
                        let personExists = false;
                        for (let option of personSelect.options) {
                            if (option.value === authorisedPerson) {
                                personExists = true;
                                break;
                            }
                        }
                        if (!personExists) {
                            const option = document.createElement('option');
                            option.value = authorisedPerson;
                            option.textContent = authorisedPerson;
                            personSelect.appendChild(option);
                        }
                        personSelect.value = authorisedPerson;
                    }
                    
                    // Show the authorised person field
                    document.getElementById('authorisedPersonField').classList.add('show');
                    document.getElementById('dataCenterInfo').innerHTML = `<strong>📍 Data Center ${dataCenterType}</strong>`;
                    
                    // Set the meeting_with value
                    if (appt.meeting_with) {
                        document.getElementById('meetingWith').value = appt.meeting_with;
                    } else {
                        document.getElementById('meetingWith').value = `${authorisedPerson} - ${dataCenterType} (Data Center)`;
                    }
                    document.getElementById('meetingWith').disabled = true;
                    
                } else if (appt.meeting_with) {
                    // For other purposes, just set the meeting_with
                    document.getElementById('meetingWith').value = appt.meeting_with;
                }
                
                showTab('checkin');
                showNotification('Visitor data loaded. Please upload photo and complete check-in.', 'info');
                window.pendingAppointmentId = appointmentId;
            }
        }

        async function checkoutVisitor(id) {
            if (!confirm('Check out this visitor?')) return;
            const result = await api('/api/visitors/' + id + '/checkout', 'PUT', { checked_out_by: currentUser });
            if (result && result.success) {
                showNotification('✅ Visitor checked out successfully!', 'success');
                loadAllData();
            } else {
                showNotification('❌ Checkout failed', 'error');
            }
        }

        async function downloadPDF(visitorId) {
            showNotification('📄 Generating compact PDF...', 'info');
            const result = await api('/api/visitors/pdf/' + visitorId, 'GET');
            if (result && result.success) {
                const basePath = getBasePath();
                const downloadUrl = basePath + '/api/visitors/pdf-download/' + visitorId;
                window.open(downloadUrl, '_blank');
                showNotification('✅ Compact PDF generated successfully!', 'success');
            } else {
                showNotification('❌ PDF generation failed: ' + (result?.error || 'Unknown error'), 'error');
            }
        }

        function showNotification(msg, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-' + type;
            alertDiv.textContent = msg;
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            document.body.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 3000);
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
                        document.getElementById('photoPreview').innerHTML = `<img src="${photoData}" alt="Visitor Photo">`;
                        showNotification('✅ Photo uploaded successfully!', 'success');
                    };
                    reader.readAsDataURL(file);
                }
            };
            input.click();
        }

        async function submitCheckin() {
            event.preventDefault();
            showLoadingOverlay();

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const company = document.getElementById('company').value.trim();
            const purpose = document.getElementById('purpose').value;
            const photo = document.getElementById('visitorPhoto').value;
            let meetingWith = document.getElementById('meetingWith').value.trim();
            const appointmentId = window.pendingAppointmentId;
            const maintenanceType = document.getElementById('maintenanceType') ? document.getElementById('maintenanceType').value : '';
            const dataCenterType = document.getElementById('dataCenterType') ? document.getElementById('dataCenterType').value : '';
            const authorisedPerson = document.getElementById('authorisedPerson') ? document.getElementById('authorisedPerson').value : '';

            if (!name || !email || !phone || !purpose) {
                hideLoadingOverlay();
                showNotification('Please fill all required fields', 'error');
                return false;
            }
            if (!photo) {
                hideLoadingOverlay();
                showNotification('Please upload a photo before check-in', 'error');
                return false;
            }

            if (purpose === 'Meeting' && !meetingWith) {
                hideLoadingOverlay();
                showNotification('Please select who you are meeting with', 'error');
                return false;
            }

            if (purpose === 'Maintenance' && !maintenanceType) {
                hideLoadingOverlay();
                showNotification('Please select maintenance type (IT or Non IT)', 'error');
                return false;
            }

            if (purpose === 'Data Center' && !dataCenterType) {
                hideLoadingOverlay();
                showNotification('Please select Data Center type (Tour or Visit)', 'error');
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

            const result = await api('/api/visitors', 'POST', {
                name, email, phone,
                company_name: company,
                vehicle_number: document.getElementById('vehicle').value.trim(),
                purpose, meeting_with: meetingWith, photo, checked_in_by: currentUser,
                maintenance_type: maintenanceType,
                data_center_type: dataCenterType
            });

            if (result && result.success) {
                if (appointmentId) {
                    await api('/api/appointments/' + appointmentId, 'DELETE');
                    window.pendingAppointmentId = null;
                }

                hideLoadingOverlay();
                showNotification('✅ Visitor checked in successfully! Compact PDF badge has been sent.', 'success');

                document.getElementById('checkinForm').reset();
                document.getElementById('visitorPhoto').value = '';
                document.getElementById('photoPreview').innerHTML = '<div class="placeholder">No photo uploaded</div>';
                document.getElementById('meetingField').classList.remove('show');
                document.getElementById('maintenanceSubtype').classList.remove('show');
                document.getElementById('dataCenterSubtype').classList.remove('show');
                document.getElementById('authorisedPersonField').classList.remove('show');
                document.getElementById('meetingWith').value = '';
                document.getElementById('meetingWith').disabled = false;
                document.getElementById('dataCenterType').value = '';
                document.getElementById('dataCenterInfo').innerHTML = '';

                loadAllData();
                showTab('active');
            } else {
                hideLoadingOverlay();
                showNotification('Check-in failed: ' + (result?.error || 'Unknown error'), 'error');
            }
            return false;
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Check if user is already logged in
        const savedUser = sessionStorage.getItem('security_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadAllData();
            autoRefreshInterval = setInterval(loadAllData, 30000);
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
    return render_template_string(SECURITY_TEMPLATE, logo_base64=logo_base64, background_base64=background_base64, company_name=COMPANY_NAME)

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
            query = "SELECT * FROM visitors WHERE 1=1"
            params = []
            if status:
                query += " AND status=%s"
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
            cursor.execute("SHOW COLUMNS FROM visitors")
            columns = [col[0] for col in cursor.fetchall()]

            insert_fields = ['visitor_id', 'name', 'email', 'phone', 'company_name', 'vehicle_number', 'purpose', 'check_in_time', 'status', 'checked_in_by']
            insert_values = [visitor_id, data['name'], data['email'], data['phone'], data.get('company_name',''), data.get('vehicle_number',''),
                           data['purpose'], check_in_time, 'in', data.get('checked_in_by','security')]

            if 'meeting_with' in columns:
                insert_fields.append('meeting_with')
                insert_values.append(data.get('meeting_with',''))
            if 'photo' in columns:
                insert_fields.append('photo')
                insert_values.append(data.get('photo',''))
            if 'data_center_type' in columns:
                insert_fields.append('data_center_type')
                insert_values.append(data.get('data_center_type',''))

            placeholders = ','.join(['%s'] * len(insert_fields))
            query = f"INSERT INTO visitors ({','.join(insert_fields)}) VALUES ({placeholders})"
            cursor.execute(query, insert_values)
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Visitor added: {data['name']}")

            visitor_data = {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'company_name': data.get('company_name', ''),
                'vehicle_number': data.get('vehicle_number', ''),
                'purpose': data['purpose'],
                'meeting_with': data.get('meeting_with', ''),
                'checked_in_by': data.get('checked_in_by', 'Security'),
                'data_center_type': data.get('data_center_type', '')
            }

            pdf_buffer = generate_visitor_pdf(visitor_data, visitor_id, data.get('photo', ''))
            send_checkin_notifications(visitor_data, visitor_id, pdf_buffer)

            return jsonify({'success': True, 'visitor_id': visitor_id})
        except Exception as e:
            print(f"Error adding visitor: {e}")
            traceback.print_exc()
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

@app.route('/api/visitors/pdf/<vid>', methods=['GET'])
def generate_pdf(vid):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM visitors WHERE visitor_id=%s OR id=%s", (vid, vid))
            visitor = cursor.fetchone()
            cursor.close()
            conn.close()

            if not visitor:
                return jsonify({'success': False, 'error': 'Visitor not found'}), 404

            pdf_buffer = generate_visitor_pdf(visitor, visitor['visitor_id'], visitor.get('photo', ''))

            if pdf_buffer:
                temp_dir = '/tmp/visitor_badges'
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                temp_path = f"{temp_dir}/visitor_badge_{visitor['visitor_id']}.pdf"
                with open(temp_path, 'wb') as f:
                    f.write(pdf_buffer.getvalue())
                return jsonify({'success': True, 'message': 'PDF generated', 'path': temp_path})
            else:
                return jsonify({'success': False, 'error': 'PDF generation failed'}), 500
        except Exception as e:
            print(f"PDF generation error: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

@app.route('/api/visitors/pdf-download/<vid>', methods=['GET'])
def download_pdf(vid):
    temp_path = f"/tmp/visitor_badges/visitor_badge_{vid}.pdf"
    if os.path.exists(temp_path):
        return send_file(temp_path, as_attachment=True, download_name=f"visitor_badge_{vid}.pdf", mimetype='application/pdf')
    else:
        conn = get_db()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM visitors WHERE visitor_id=%s OR id=%s", (vid, vid))
                visitor = cursor.fetchone()
                cursor.close()
                conn.close()

                if visitor:
                    pdf_buffer = generate_visitor_pdf(visitor, visitor['visitor_id'], visitor.get('photo', ''))

                    if pdf_buffer:
                        temp_dir = '/tmp/visitor_badges'
                        if not os.path.exists(temp_dir):
                            os.makedirs(temp_dir)
                        temp_path = f"{temp_dir}/visitor_badge_{vid}.pdf"
                        with open(temp_path, 'wb') as f:
                            f.write(pdf_buffer.getvalue())

                        return send_file(temp_path, as_attachment=True, download_name=f"visitor_badge_{vid}.pdf", mimetype='application/pdf')
            except Exception as e:
                print(f"PDF download error: {e}")
                return jsonify({'error': str(e)}), 500

        return jsonify({'error': 'PDF not found'}), 404

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    status = request.args.get('status', '')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Explicitly select all columns including data_center_type
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
            print(f"Error: {e}")
            traceback.print_exc()
    return jsonify([])

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
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

@app.route('/api/appointments/<aid>', methods=['GET'])
def get_appointment(aid):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Explicitly select all columns including data_center_type
            cursor.execute("""
                SELECT appointment_id, id, name, email, phone, company_name, vehicle_number, 
                       purpose, meeting_with, appointment_date, notes, status, created_by, 
                       maintenance_type, is_group, group_members, data_center_type, rejection_reason 
                FROM appointments 
                WHERE appointment_id=%s OR id=%s
            """, (aid, aid))
            appt = cursor.fetchone()
            cursor.close()
            conn.close()
            if appt and appt.get('appointment_date'):
                appt['appointment_date'] = str(appt['appointment_date'])
            return jsonify(appt)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
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
    try:
        import PIL
        print("✅ Pillow is installed")
    except ImportError:
        print("⚠️ Installing Pillow...")
        os.system("pip install pillow")

    os.makedirs('/tmp/visitor_badges', exist_ok=True)

    print("=" * 60)
    print("🔒 Security Service running on port 8081")
    print("   URL: http://localhost:8081")
    print("   Login: security / security123")
    print("=" * 60)
    app.run(host='127.0.0.1', port=8081, debug=False)
