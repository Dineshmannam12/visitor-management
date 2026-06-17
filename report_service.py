from flask import Flask, request, jsonify, render_template_string, send_file, session
from flask_cors import CORS
from db_utils import get_db
from datetime import datetime, timedelta
import io
import base64
import os
import pandas as pd
from config import get_logo_base64, COMPANY_NAME
import traceback

app = Flask(__name__)
app.secret_key = 'report_secret_key_2024'
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
        .card h3 { color: #1e3c72; margin-bottom: 15px; }
        
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

        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: flex-end;
        }
        .filter-group .filter-item {
            flex: 1;
            min-width: 150px;
        }
        .filter-group label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin-bottom: 5px;
        }
        .filter-group input, .filter-group select {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.9);
        }
        .filter-group input:focus, .filter-group select:focus {
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 0 3px rgba(30, 60, 114, 0.1);
            background: white;
        }
        .filter-group button {
            padding: 10px 24px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        .filter-group button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .filter-group .btn-export {
            background: linear-gradient(135deg, #00b894, #009432);
        }
        .filter-group .btn-export:hover {
            box-shadow: 0 4px 12px rgba(0, 184, 148, 0.4);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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
            font-size: 28px;
            font-weight: bold;
            color: #1e3c72;
        }
        .stat-card .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }

        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        table th {
            background: #1e3c72;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }
        table td {
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        table tr:hover {
            background: #f5f5f5;
        }
        .badge-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-status.pending { background: #ff9a44; color: white; }
        .badge-status.approved { background: #00b894; color: white; }
        .badge-status.rejected { background: #ff7675; color: white; }
        .badge-status.in { background: #2196F3; color: white; }
        .badge-status.out { background: #9e9e9e; color: white; }

        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .no-data .icon {
            font-size: 48px;
            margin-bottom: 10px;
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
            .filter-group {
                flex-direction: column;
            }
            .filter-group .filter-item {
                min-width: 100%;
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
                            <div class="brand-icon">📊</div>
                            <h1>Reports Portal</h1>
                            <p>Pi Datacenters Analytics</p>
                        </div>
                        <div class="login-features">
                            <div class="feature-item">
                                <span class="feature-icon">📈</span>
                                <span>Visitor Analytics</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">📋</span>
                                <span>Appointment Reports</span>
                            </div>
                            <div class="feature-item">
                                <span class="feature-icon">📤</span>
                                <span>Export Data</span>
                            </div>
                        </div>
                        <div class="login-footer-links">
                            <a href="/" class="back-link">← Back to Gateway</a>
                        </div>
                    </div>
                    <div class="login-right">
                        <div class="login-header">
                            <div class="logo-container">
                                {% if logo_base64 %}
                                    <img src="{{ logo_base64 }}" alt="PI Data Centers" class="logo-img">
                                {% endif %}
                            </div>
                            <h2>Reports Dashboard</h2>
                            <p>View and export visitor reports</p>
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
                📊 Pi Datacenters <span>Reports Portal</span>
            </div>
            <div class="top-bar-right">
                <a href="/">🏠 Gateway</a>
                <span>👤 <span id="currentUser"></span></span>
                <button class="logout-btn" onclick="doLogout()" style="background: #e74c3c; color: white; padding: 8px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.3s ease;">🚪 Logout</button>
            </div>
        </div>

        <div class="container">
            <div class="card">
                <h2>📊 Visitor Reports</h2>
                <div class="filter-group">
                    <div class="filter-item">
                        <label>📅 Date Range</label>
                        <input type="date" id="startDate">
                    </div>
                    <div class="filter-item">
                        <label>📅 To</label>
                        <input type="date" id="endDate">
                    </div>
                    <div class="filter-item">
                        <label>📋 Purpose</label>
                        <select id="filterPurpose">
                            <option value="">All Purposes</option>
                            <option value="Data Center">Data Center</option>
                            <option value="Meeting">Meeting</option>
                            <option value="Maintenance">Maintenance</option>
                        </select>
                    </div>
                    <div class="filter-item">
                        <label>📊 Status</label>
                        <select id="filterStatus">
                            <option value="">All Status</option>
                            <option value="in">Checked In</option>
                            <option value="out">Checked Out</option>
                            <option value="approved">Approved</option>
                            <option value="pending">Pending</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </div>
                    <div class="filter-item" style="flex: 0 0 auto;">
                        <button onclick="applyFilters()">🔍 Apply Filters</button>
                    </div>
                    <div class="filter-item" style="flex: 0 0 auto;">
                        <button onclick="exportExcel()" class="btn-export">📤 Export Excel</button>
                    </div>
                </div>
            </div>

            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <h4>👥 Total Visitors</h4>
                    <p id="totalVisitors">0</p>
                    <div class="stat-label">All time</div>
                </div>
                <div class="stat-card">
                    <h4>🏢 Currently Inside</h4>
                    <p id="insideCount">0</p>
                    <div class="stat-label">Active visitors</div>
                </div>
                <div class="stat-card">
                    <h4>✅ Today's Check-ins</h4>
                    <p id="todayCheckins">0</p>
                    <div class="stat-label">Today</div>
                </div>
                <div class="stat-card">
                    <h4>📋 Total Appointments</h4>
                    <p id="totalAppointments">0</p>
                    <div class="stat-label">All time</div>
                </div>
            </div>

            <div class="card">
                <h2>📋 Visitor List</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Company</th>
                                <th>Purpose</th>
                                <th>Meeting With</th>
                                <th>Check In</th>
                                <th>Check Out</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="visitorTableBody">
                            <tr>
                                <td colspan="10" class="no-data">
                                    <div class="icon">📭</div>
                                    <div>No visitors found</div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let currentData = [];

        function getBasePath() {
            const pathname = window.location.pathname;
            if (pathname.startsWith('/report/')) {
                return '/report';
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

        async function doLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const loginAlert = document.getElementById('loginAlert');

            if (!username || !password) {
                loginAlert.textContent = 'Please enter username and password';
                loginAlert.className = 'alert alert-error';
                loginAlert.style.display = 'block';
                loginAlert.style.background = '#f8d7da';
                loginAlert.style.color = '#721c24';
                loginAlert.style.padding = '12px';
                loginAlert.style.borderRadius = '8px';
                loginAlert.style.marginBottom = '15px';
                loginAlert.style.borderLeft = '4px solid #dc3545';
                return;
            }

            loginAlert.style.display = 'none';

            const result = await api('/api/login', 'POST', { username, password });
            if (result && result.success) {
                currentUser = result.username;
                sessionStorage.setItem('report_user', username);
                document.getElementById('currentUser').textContent = username;
                document.getElementById('loginPage').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                loadDashboard();
                loadVisitors();
            } else {
                loginAlert.textContent = 'Invalid credentials or unauthorized access';
                loginAlert.className = 'alert alert-error';
                loginAlert.style.display = 'block';
                loginAlert.style.background = '#f8d7da';
                loginAlert.style.color = '#721c24';
                loginAlert.style.padding = '12px';
                loginAlert.style.borderRadius = '8px';
                loginAlert.style.marginBottom = '15px';
                loginAlert.style.borderLeft = '4px solid #dc3545';
            }
        }

        function doLogout() {
            currentUser = null;
            sessionStorage.removeItem('report_user');
            document.getElementById('loginPage').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
            const loginAlert = document.getElementById('loginAlert');
            loginAlert.style.display = 'none';
        }

        async function loadDashboard() {
            const stats = await api('/api/stats');
            if (stats) {
                document.getElementById('totalVisitors').textContent = stats.totalVisitors || 0;
                document.getElementById('insideCount').textContent = stats.inside || 0;
                document.getElementById('todayCheckins').textContent = stats.todayCheckins || 0;
                document.getElementById('totalAppointments').textContent = stats.totalAppointments || 0;
            }
        }

        async function loadVisitors() {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const purpose = document.getElementById('filterPurpose').value;
            const status = document.getElementById('filterStatus').value;

            let url = '/api/visitors/report?';
            if (startDate) url += `start_date=${startDate}&`;
            if (endDate) url += `end_date=${endDate}&`;
            if (purpose) url += `purpose=${purpose}&`;
            if (status) url += `status=${status}&`;

            const visitors = await api(url);
            currentData = visitors || [];

            const tbody = document.getElementById('visitorTableBody');
            if (!currentData || currentData.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="10" class="no-data">
                            <div class="icon">📭</div>
                            <div>No visitors found</div>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = currentData.map((v, i) => {
                let statusBadge = '';
                if (v.status === 'in') statusBadge = '<span class="badge-status in">IN</span>';
                else if (v.status === 'out') statusBadge = '<span class="badge-status out">OUT</span>';
                else if (v.status === 'approved') statusBadge = '<span class="badge-status approved">APPROVED</span>';
                else if (v.status === 'pending') statusBadge = '<span class="badge-status pending">PENDING</span>';
                else if (v.status === 'rejected') statusBadge = '<span class="badge-status rejected">REJECTED</span>';
                else statusBadge = `<span class="badge-status">${v.status || 'N/A'}</span>`;

                return `
                    <tr>
                        <td>${i + 1}</td>
                        <td><strong>${escapeHtml(v.name)}</strong></td>
                        <td>${escapeHtml(v.email)}</td>
                        <td>${escapeHtml(v.phone)}</td>
                        <td>${escapeHtml(v.company_name || 'N/A')}</td>
                        <td>${escapeHtml(v.purpose || 'N/A')}</td>
                        <td>${escapeHtml(v.meeting_with || 'N/A')}</td>
                        <td>${v.check_in_time ? new Date(v.check_in_time).toLocaleString() : 'N/A'}</td>
                        <td>${v.check_out_time ? new Date(v.check_out_time).toLocaleString() : 'N/A'}</td>
                        <td>${statusBadge}</td>
                    </tr>
                `;
            }).join('');
        }

        function applyFilters() {
            loadVisitors();
        }

        async function exportExcel() {
            if (!currentData || currentData.length === 0) {
                alert('No data to export. Please apply filters first.');
                return;
            }

            const response = await fetch('/report/api/export/excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: currentData })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `visitor_report_${new Date().toISOString().slice(0,10)}.xlsx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                alert('Failed to export data. Please try again.');
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Set default dates
        const today = new Date().toISOString().slice(0,10);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        document.getElementById('startDate').value = weekAgo.toISOString().slice(0,10);
        document.getElementById('endDate').value = today;

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

        // Check if user is already logged in
        const savedUser = sessionStorage.getItem('report_user');
        if (savedUser) {
            currentUser = savedUser;
            document.getElementById('currentUser').textContent = savedUser;
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
            loadDashboard();
            loadVisitors();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    logo_base64 = get_logo_base64()
    background_base64 = get_background_base64()
    return render_template_string(REPORT_TEMPLATE, logo_base64=logo_base64, background_base64=background_base64, company_name=COMPANY_NAME)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'report', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role IN ('admin', 'security')", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return jsonify({'success': True, 'username': user['username'], 'role': user['role']})
        except Exception as e:
            print(f"Login error: {e}")
    return jsonify({'success': False}), 401

@app.route('/api/stats')
def get_stats():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM visitors")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as inside FROM visitors WHERE status='in'")
            inside = cursor.fetchone()['inside']
            
            cursor.execute("SELECT COUNT(*) as today FROM visitors WHERE DATE(check_in_time)=CURDATE()")
            today = cursor.fetchone()['today']
            
            cursor.execute("SELECT COUNT(*) as total_appointments FROM appointments")
            total_appointments = cursor.fetchone()['total_appointments']
            
            cursor.close()
            conn.close()
            return jsonify({
                'totalVisitors': total,
                'inside': inside,
                'todayCheckins': today,
                'totalAppointments': total_appointments
            })
        except Exception as e:
            print(f"Error getting stats: {e}")
    return jsonify({'totalVisitors': 0, 'inside': 0, 'todayCheckins': 0, 'totalAppointments': 0})

@app.route('/api/visitors/report')
def get_visitors_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    purpose = request.args.get('purpose')
    status = request.args.get('status')
    
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT v.*, 
                       a.status as appointment_status, a.purpose as appointment_purpose,
                       a.meeting_with as appointment_meeting_with
                FROM visitors v
                LEFT JOIN appointments a ON v.email = a.email
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(v.check_in_time) >= %s"
                params.append(start_date)
            if end_date:
                query += " AND DATE(v.check_in_time) <= %s"
                params.append(end_date)
            if purpose:
                query += " AND v.purpose = %s"
                params.append(purpose)
            if status:
                if status == 'approved':
                    query += " AND a.status = 'approved'"
                elif status == 'pending':
                    query += " AND a.status = 'pending'"
                elif status == 'rejected':
                    query += " AND a.status = 'rejected'"
                else:
                    query += " AND v.status = %s"
                    params.append(status)
            
            query += " ORDER BY v.check_in_time DESC"
            cursor.execute(query, params)
            visitors = cursor.fetchall()
            cursor.close()
            conn.close()
            
            for v in visitors:
                if v.get('check_in_time'):
                    v['check_in_time'] = str(v['check_in_time'])
                if v.get('check_out_time'):
                    v['check_out_time'] = str(v['check_out_time'])
                # Use appointment purpose if available, else visitor purpose
                if v.get('appointment_purpose'):
                    v['purpose'] = v['appointment_purpose']
                if v.get('appointment_meeting_with'):
                    v['meeting_with'] = v['appointment_meeting_with']
                if v.get('appointment_status'):
                    v['status'] = v['appointment_status']
            
            return jsonify(visitors)
        except Exception as e:
            print(f"Error getting visitors report: {e}")
            traceback.print_exc()
    return jsonify([])

@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    data = request.json.get('data', [])
    if not data:
        return jsonify({'error': 'No data to export'}), 400
    
    try:
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Visitors')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'visitor_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        print(f"Export error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("📊 Reports Service running on port 8084")
    print("   URL: http://localhost:8084")
    print("   Login: admin / admin123 or security / security123")
    print("=" * 60)
    app.run(host='127.0.0.1', port=8084, debug=False)
