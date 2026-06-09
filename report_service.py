from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime
from config import get_logo_base64, COMPANY_NAME

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

REPORT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reports Portal - PI Data Centers</title>
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
        .stat-card h3 { font-size: 12px; color: #666; text-transform: uppercase; margin-bottom: 5px; }
        .stat-card p { font-size: 28px; font-weight: bold; color: #1e3c72; }
        .filter-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filter-bar select, .filter-bar input, .filter-bar button {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .filter-bar select { background: white; }
        .filter-bar input { width: 250px; }
        button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-1px); }
        .table-container {
            overflow-x: auto;
            margin-top: 15px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #1e3c72;
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            white-space: nowrap;
        }
        td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge.in { background: #2196F3; color: white; }
        .badge.out { background: #9e9e9e; color: white; }
        .login-box {
            max-width: 400px;
            margin: 50px auto;
        }
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
        .logout-btn { background: #f44336; padding: 8px 20px; }
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
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: none;
        }
        .alert-success { background: #d4edda; color: #155724; display: block; }
        .alert-error { background: #f8d7da; color: #721c24; display: block; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .record-count {
            margin-bottom: 15px;
            padding: 10px;
            background: #f0f7ff;
            border-radius: 8px;
            font-size: 14px;
        }
        .record-count strong {
            color: #1e3c72;
        }
    </style>
</head>
<body>
    <div id="loginPage">
        <div class="container">
            <div class="card login-box">
                <div class="logo-container">
                    {% if logo_base64 %}
                        <img src="{{ logo_base64 }}" alt="PI Data Centers Logo" class="logo-img">
                    {% else %}
                        <div style="font-size: 60px;">📊</div>
                    {% endif %}
                    <h2 class="login-title">Pi Data Centers Reports Portal Login</h2>
                    <p class="login-subtitle">Access Reports and Analytics</p>
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
            <div class="brand"><strong>Pi Datacenters - Report Portal</strong></div>
            <span>👤 <span id="currentUser"></span></span>
            <button class="logout-btn" onclick="doLogout()">Logout</button>
        </div>
        <div class="container">
            <h1 style="color: white;">📊 Reports & Analytics</h1>
            
            <div class="card">
                <h2>📈 Visitor Statistics</h2>
                <div class="stats" id="stats">
                    <div class="loading">Loading statistics...</div>
                </div>
            </div>

            <div class="card">
                <h2>📋 Visitor Records</h2>
                <div class="filter-bar">
                    <select id="period" onchange="loadRecords()">
                        <option value="today">Today</option>
                        <option value="yesterday">Yesterday</option>
                        <option value="week">This Week</option>
                        <option value="month">This Month</option>
                        <option value="year">This Year</option>
                        <option value="all" selected>All Time</option>
                    </select>
                    <input type="text" id="search" placeholder="🔍 Search by name, email, phone..." onkeyup="loadRecords()">
                    <button class="btn-small" onclick="exportRecords()" style="background: #2196F3;">📥 Export CSV</button>
                    <button class="btn-small" onclick="emailReport()" style="background: #9c27b0;">📧 Email Report</button>
                    <button class="btn-small" onclick="loadRecords()" style="background: #607d8b;">🔄 Refresh</button>
                </div>
                <div id="recordCount" class="record-count"></div>
                <div class="table-container">
                    <div id="recordsList">
                        <div class="loading">Loading records...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;

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

        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            if (!username || !password) {
                alert('Please enter credentials');
                return;
            }
            const result = await api('/api/login', 'POST', { username, password });
            if (result && result.success) {
                currentUser = result.username;
                sessionStorage.setItem('report_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadStats();
                loadRecords();
            } else {
                alert('Invalid credentials');
            }
        }

        function doLogout() {
            currentUser = null;
            sessionStorage.removeItem('report_user');
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
        }

        async function loadStats() {
            const stats = await api('/api/stats');
            if (stats) {
                const statsDiv = document.getElementById('stats');
                statsDiv.innerHTML = `
                    <div class="stat-card"><h3>Total Visitors</h3><p>${stats.total || 0}</p></div>
                    <div class="stat-card"><h3>Currently Inside</h3><p>${stats.inside || 0}</p></div>
                    <div class="stat-card"><h3>Today's Check-ins</h3><p>${stats.today || 0}</p></div>
                    <div class="stat-card"><h3>Today's Check-outs</h3><p>${stats.checkedOutToday || 0}</p></div>
                    <div class="stat-card"><h3>This Week</h3><p>${stats.thisWeek || 0}</p></div>
                    <div class="stat-card"><h3>This Month</h3><p>${stats.thisMonth || 0}</p></div>
                `;
            }
        }

        async function loadRecords() {
            const period = document.getElementById('period').value;
            const search = document.getElementById('search').value;
            const data = await api(`/api/records?period=${period}&search=${encodeURIComponent(search)}`);
            displayRecords(data);
        }

        function displayRecords(data) {
            const container = document.getElementById('recordsList');
            const countDiv = document.getElementById('recordCount');
            
            if (!data || !data.visitors || data.visitors.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:#999;padding:40px;">No records found</div>';
                countDiv.innerHTML = '';
                return;
            }
            
            // Update record count
            const periodName = document.getElementById('period').options[document.getElementById('period').selectedIndex].text;
            countDiv.innerHTML = `<strong>📊 Found ${data.visitors.length} record(s)</strong> for ${periodName} ${document.getElementById('search').value ? 'matching "' + escapeHtml(document.getElementById('search').value) + '"' : ''}`;
            
            // Create table with proper headers
            let html = `<table><thead>
                <tr>
                    <th style="width: 50px;">#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Vehicle</th>
                    <th>Purpose</th>
                    <th>Meeting With</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Duration</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>`;
            
            data.visitors.forEach((v, i) => {
                // Calculate duration
                let duration = '-';
                if (v.check_in_time && v.check_out_time) {
                    try {
                        const checkIn = new Date(v.check_in_time);
                        const checkOut = new Date(v.check_out_time);
                        const diffMs = checkOut - checkIn;
                        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                        if (diffHours > 0 || diffMinutes > 0) {
                            duration = `${diffHours}h ${diffMinutes}m`;
                        }
                    } catch(e) {
                        duration = '-';
                    }
                }
                
                const badge = v.status === 'in' ? '<span class="badge in">● INSIDE</span>' : '<span class="badge out">● OUT</span>';
                const checkInTime = v.check_in_time ? new Date(v.check_in_time).toLocaleString() : '-';
                const checkOutTime = v.check_out_time ? new Date(v.check_out_time).toLocaleString() : '-';
                
                html += `<tr>
                    <td>${i + 1}</td>
                    <td><strong>${escapeHtml(v.name)}</strong></td>
                    <td>${escapeHtml(v.email)}</td>
                    <td>${escapeHtml(v.phone || '-')}</td>
                    <td>${escapeHtml(v.vehicle_number || '-')}</td>
                    <td>${escapeHtml(v.purpose || '-')}</td>
                    <td>${escapeHtml(v.meeting_with || '-')}</td>
                    <td>${checkInTime}</td>
                    <td>${checkOutTime}</td>
                    <td>${duration}</td>
                    <td>${badge}</td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function exportRecords() {
            const period = document.getElementById('period').value;
            const search = document.getElementById('search').value;
            window.open(`/api/records/export?period=${period}&search=${encodeURIComponent(search)}`, '_blank');
        }

        async function emailReport() {
            const period = document.getElementById('period').value;
            const result = await api('/api/records/email', 'POST', { period });
            if (result && result.success) {
                alert('📧 Report sent successfully!');
            } else {
                alert('❌ Failed to send report. Please check email settings.');
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Check for existing session
        const savedUser = sessionStorage.getItem('report_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadStats();
            loadRecords();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    return render_template_string(REPORT_TEMPLATE, logo_base64=logo_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'report', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", 
                         (data['username'], data['password']))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return jsonify({'success': True, 'username': user['username'], 'role': user['role']})
        except Exception as e:
            print(f"Login error: {e}")
    return jsonify({'success': False}), 401

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as c FROM visitors")
            total = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE status='in'")
            inside = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE DATE(check_in_time)=CURDATE()")
            today = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE DATE(check_out_time)=CURDATE() AND status='out'")
            checked_out = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE YEARWEEK(check_in_time)=YEARWEEK(CURDATE())")
            this_week = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM visitors WHERE MONTH(check_in_time)=MONTH(CURDATE()) AND YEAR(check_in_time)=YEAR(CURDATE())")
            this_month = cursor.fetchone()['c']
            cursor.close()
            conn.close()
            return jsonify({'total': total, 'inside': inside, 'today': today, 'checkedOutToday': checked_out, 
                          'thisWeek': this_week, 'thisMonth': this_month})
        except Exception as e:
            print(f"Stats error: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'total': 0, 'inside': 0, 'today': 0, 'checkedOutToday': 0, 'thisWeek': 0, 'thisMonth': 0})

@app.route('/api/records', methods=['GET'])
def get_records():
    period = request.args.get('period', 'all')
    search = request.args.get('search', '')
    conn = get_db()
    if conn:
        try:
            query = "SELECT * FROM visitors WHERE 1=1"
            params = []
            if period == 'today':
                query += " AND DATE(check_in_time) = CURDATE()"
            elif period == 'yesterday':
                query += " AND DATE(check_in_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)"
            elif period == 'week':
                query += " AND YEARWEEK(check_in_time) = YEARWEEK(CURDATE())"
            elif period == 'month':
                query += " AND MONTH(check_in_time) = MONTH(CURDATE()) AND YEAR(check_in_time) = YEAR(CURDATE())"
            elif period == 'year':
                query += " AND YEAR(check_in_time) = YEAR(CURDATE())"
            if search:
                query += " AND (name LIKE %s OR email LIKE %s OR phone LIKE %s OR vehicle_number LIKE %s)"
                s = f"%{search}%"
                params.extend([s, s, s, s])
            query += " ORDER BY check_in_time DESC LIMIT 1000"
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            visitors = cursor.fetchall()
            cursor.close()
            conn.close()
            for v in visitors:
                if v.get('check_in_time'):
                    v['check_in_time'] = str(v['check_in_time'])
                if v.get('check_out_time'):
                    v['check_out_time'] = str(v['check_out_time'])
            return jsonify({'visitors': visitors})
        except Exception as e:
            print(f"Records error: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'visitors': []})

@app.route('/api/records/export', methods=['GET'])
def export_records():
    period = request.args.get('period', 'all')
    search = request.args.get('search', '')
    conn = get_db()
    visitors = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM visitors WHERE 1=1"
            params = []
            if period == 'today':
                query += " AND DATE(check_in_time) = CURDATE()"
            elif period == 'yesterday':
                query += " AND DATE(check_in_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)"
            elif period == 'week':
                query += " AND YEARWEEK(check_in_time) = YEARWEEK(CURDATE())"
            elif period == 'month':
                query += " AND MONTH(check_in_time) = MONTH(CURDATE()) AND YEAR(check_in_time) = YEAR(CURDATE())"
            elif period == 'year':
                query += " AND YEAR(check_in_time) = YEAR(CURDATE())"
            if search:
                query += " AND (name LIKE %s OR email LIKE %s OR phone LIKE %s)"
                s = f"%{search}%"
                params.extend([s, s, s])
            query += " ORDER BY check_in_time DESC"
            cursor.execute(query, params)
            visitors = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Export error: {e}")
    
    # Generate CSV with proper headers
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['S.No', 'Name', 'Email', 'Phone', 'Vehicle Number', 'Purpose', 'Meeting With', 'Check In Time', 'Check Out Time', 'Duration', 'Status'])
    
    # Write data rows
    for idx, v in enumerate(visitors, 1):
        # Calculate duration
        duration = ''
        if v.get('check_in_time') and v.get('check_out_time'):
            try:
                ci = datetime.strptime(str(v['check_in_time'])[:19], '%Y-%m-%d %H:%M:%S')
                co = datetime.strptime(str(v['check_out_time'])[:19], '%Y-%m-%d %H:%M:%S')
                diff = co - ci
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            except:
                duration = 'N/A'
        
        writer.writerow([
            idx,
            v.get('name', ''),
            v.get('email', ''),
            v.get('phone', ''),
            v.get('vehicle_number', ''),
            v.get('purpose', ''),
            v.get('meeting_with', ''),
            v.get('check_in_time', ''),
            v.get('check_out_time', ''),
            duration,
            'IN' if v.get('status') == 'in' else 'OUT'
        ])
    
    output.seek(0)
    period_name = period
    if period == 'today': period_name = 'Today'
    elif period == 'yesterday': period_name = 'Yesterday'
    elif period == 'week': period_name = 'This_Week'
    elif period == 'month': period_name = 'This_Month'
    elif period == 'year': period_name = 'This_Year'
    else: period_name = 'All_Time'
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=visitors_report_{period_name}.csv"}
    )

@app.route('/api/records/email', methods=['POST'])
def email_records():
    data = request.json
    period = data.get('period', 'all')
    # This is a placeholder - you can implement actual email sending here
    return jsonify({'success': True, 'message': 'Report email feature - Configure SMTP settings to enable'})

if __name__ == '__main__':
    print("=" * 60)
    print("📊 Report Service running on port 8084")
    print("   URL: http://localhost:8084")
    print("   Login: reporter / reporter123")
    print("   Features: Statistics, Records, Search, Export CSV")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8084, debug=False)
