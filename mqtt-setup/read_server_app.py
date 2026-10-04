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

r('cat ~/tetasco-connect/backend/main.py', '1. backend/main.py')
r('cat ~/tetasco-connect/nginx/*.conf 2>/dev/null || ls ~/tetasco-connect/nginx/', '2. Nginx config')
r('cat ~/tetasco-connect/docker-compose.yml', '3. docker-compose.yml')
r('cat ~/tetasco-connect/.env', '4. .env')
r('ls ~/tetasco-connect/backend/', '5. backend dir')

sv.close()
