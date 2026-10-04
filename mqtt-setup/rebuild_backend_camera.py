import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# Cek apakah camera endpoint ada di container
r('docker exec tetasco-backend grep -n "camera/push\|camera/stream\|camera_push" /app/main.py | head -10',
  '1. Camera endpoints di container')

# Cek nginx WebSocket header
r('docker exec tetasco-nginx grep -n "camera\|Upgrade\|Connection" /etc/nginx/nginx.conf | head -20',
  '2. Nginx camera+WS config')

# Rebuild backend dengan camera endpoints
r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5',
  '3. Rebuild backend', timeout=120)

# Fix nginx: pastikan WebSocket Connection header benar
i,o,e = sv.exec_command('cat ~/tetasco-connect/nginx/nginx.conf')
nginx = o.read().decode('utf-8','replace')

# Fix: Connection $http_upgrade → Connection "upgrade"
nginx_fixed = nginx.replace(
    'proxy_set_header       Connection        $http_upgrade;\n            add_header         X-Accel-Buffering no;',
    'proxy_set_header       Connection        "upgrade";\n            add_header         X-Accel-Buffering no;'
)
if nginx_fixed != nginx:
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(nginx_fixed.encode()), '/home/telur/tetasco-connect/nginx/nginx.conf')
    sftp.close()
    print('[OK] Nginx WebSocket Connection header fixed')
else:
    print('[INFO] Nginx WS header OK atau tidak perlu fix')

# Restart semua
r('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -8',
  '4. Docker compose up', timeout=30)
time.sleep(12)

r('docker ps --format "{{.Names}}\\t{{.Status}}"', '5. Container status')
r('curl -s http://localhost:8000/api/health', '6. Backend health')
r('curl -s "http://localhost:8000/api/tetasco/1/camera/stats"', '7. Camera stats')

# Verify WebSocket endpoint ada
r('docker exec tetasco-backend grep -c "camera_push\|camera/push" /app/main.py || echo "0"',
  '8. WS endpoint count di container')

sv.close()
