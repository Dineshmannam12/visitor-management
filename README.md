installation steps:

1. sudo apt update -y && apt upgrade -y

2. Install Python packages through apt

   sudo apt install python3-flask python3-flask-cors python3-mysql.connector

4. Install  database:
   
    sudo apt install mariadb-server mariadb-client

6. create a password for root user for database:
   
    sudo mysql_secure_installation

8. create a tables in mariadb

   mysql -u root -p

   -- Create database
CREATE DATABASE IF NOT EXISTS visitor_management;
USE visitor_management;

-- Create visitors table
CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    vehicle_number VARCHAR(50),
    purpose VARCHAR(100),
    meeting_with VARCHAR(100),
    check_in_time DATETIME NOT NULL,
    check_out_time DATETIME,
    status VARCHAR(20) DEFAULT 'in',
    checked_in_by VARCHAR(50),
    checked_out_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    vehicle_number VARCHAR(50),
    purpose VARCHAR(100),
    meeting_with VARCHAR(100),
    appointment_date DATETIME NOT NULL,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'staff'
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT
);

-- Insert default users
INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('security', 'security123', 'security'),
('reception', 'reception123', 'reception');

-- Insert default settings
INSERT INTO settings (setting_key, setting_value)
VALUES ('manager_email', 'manager@pidatacenters.com');

-- Create application user
CREATE USER IF NOT EXISTS 'visitor_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_STRONG_PASSWORD';

GRANT ALL PRIVILEGES ON visitor_management.* TO 'visitor_app'@'localhost';

FLUSH PRIVILEGES;
EXIT;

6. fetch the code from github to local server.

7. Run the application using

8.  python3 run_all.py
   

