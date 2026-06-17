import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime
from config import DB_CONFIG

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create visitors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    visitor_id VARCHAR(50) UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    vehicle_number VARCHAR(100),
                    purpose VARCHAR(100),
                    meeting_with VARCHAR(255),
                    photo LONGTEXT,
                    check_in_time DATETIME,
                    check_out_time DATETIME,
                    status VARCHAR(20) DEFAULT 'in',
                    checked_in_by VARCHAR(100),
                    checked_out_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    appointment_id VARCHAR(50) UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    vehicle_number VARCHAR(100),
                    purpose VARCHAR(100),
                    meeting_with VARCHAR(255),
                    appointment_date DATETIME,
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    rejection_reason TEXT,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE,
                    setting_value TEXT
                )
            """)
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE,
                    password VARCHAR(255),
                    role VARCHAR(50)
                )
            """)
            
            # Insert default users
            cursor.execute("SELECT * FROM users WHERE username='admin'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                             ('admin', 'admin123', 'admin'))
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                             ('security', 'security123', 'security'))
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                             ('reception', 'reception123', 'reception'))
                cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                             ('reporter', 'reporter123', 'reporter'))
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database initialized successfully")
            return True
        except Error as e:
            print(f"DB Init Error: {e}")
            return False
    return False

def generate_visitor_id():
    return str(uuid.uuid4())[:8]

def generate_appointment_id():
    return str(uuid.uuid4())[:8]
