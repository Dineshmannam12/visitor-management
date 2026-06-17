# ==================== RUN ALL SERVICES (run_all.py) ====================
import subprocess
import time
import webbrowser
import os
import sys

def run_services():
    """Launch all microservices"""
    services = [
        ('API Gateway', 'gateway.py', 8080),
        ('Security Service', 'security_service.py', 8081),
        ('Admin Service', 'admin_service.py', 8082),
        ('Visitor Service', 'visitor_service.py', 8083),
        ('Report Service', 'report_service.py', 8084)
    ]
    
    processes = []
    
    print("=" * 60)
    print("🚀 Starting PI Data Centers - Visitor Management System")
    print("=" * 60)
    
    for name, script, port in services:
        print(f"Starting {name} on port {port}...")
        try:
            # Run each service as a separate process
            process = subprocess.Popen([sys.executable, script], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
            processes.append(process)
            time.sleep(2)  # Wait for service to start
            print(f"✅ {name} started successfully on http://localhost:{port}")
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All services are running!")
    print("=" * 60)
    print("\nAccess the system:")
    print(f"  🌐 API Gateway:    http://localhost:8080")
    print(f"  🔒 Security:       http://localhost:8081  (security / security123)")
    print(f"  👑 Admin:          http://localhost:8082  (admin / admin123)")
    print(f"  📝 Visitor:        http://localhost:8083")
    print(f"  📊 Reports:        http://localhost:8084")
    print("\nPress Ctrl+C to stop all services...")
    
    # Open browser to API Gateway
    webbrowser.open('http://localhost:8080')
    
    try:
        # Wait for all processes
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all services...")
        for p in processes:
            p.terminate()
        print("✅ All services stopped")

if __name__ == '__main__':
    # Initialize database first
    from db_utils import init_db
    init_db()
    
    run_services()
