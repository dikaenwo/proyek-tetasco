import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Eksplorasi struktur app
r('ls -la ~/tetasco-connect/', '1. tetasco-connect dir')
r('ls -la ~/Penetas-Telur/', '2. Penetas-Telur dir')
r('find ~/tetasco-connect -name "*.py" | head -20', '3. Python files')
r('cat ~/tetasco-connect/main.py | head -80', '4. main.py (awal)')
r('grep -n "camera\|stream\|tetasco\|claim\|router\|app\." ~/tetasco-connect/main.py | head -30', '5. Routes di main.py')
r('ls ~/tetasco-connect/routers/ 2>/dev/null || ls ~/tetasco-connect/routes/ 2>/dev/null || echo "no routers dir"', '6. Routers dir')
r('cat /etc/nginx/nginx.conf 2>/dev/null | head -40 || cat /etc/nginx/sites-enabled/* 2>/dev/null | head -40', '7. Nginx config')
r('ls -la ~/tetasco-connect/', '8. tetasco-connect files')

sv.close()
