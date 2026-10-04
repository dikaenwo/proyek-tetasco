import paramiko, sys, io, time, re
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

# Baca nginx.conf dari container
i,o,e = sv.exec_command('cat ~/tetasco-connect/nginx/nginx.conf')
nginx = o.read().decode('utf-8','replace')
print(f'nginx.conf: {len(nginx)} chars')

# Ganti seluruh camera location block dengan versi yang benar
OLD_CAMERA_BLOCK = re.search(
    r'# ── Camera Streaming.*?(?=\n\s+# ── REST|location /api/)',
    nginx, re.DOTALL
)
if OLD_CAMERA_BLOCK:
    print(f'[OK] Found camera block: {OLD_CAMERA_BLOCK.start()}-{OLD_CAMERA_BLOCK.end()}')
else:
    print('[WARN] Camera block tidak ditemukan')

CAMERA_BLOCK_CORRECT = '''        # ── Camera Streaming (MJPEG + WebSocket push) ─────────────────────────
        location ~ ^/api/tetasco/[0-9]+/camera/ {
            set $backend_upstream "http://tetasco-backend:8000";
            proxy_pass         $backend_upstream;
            proxy_http_version 1.1;
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   Upgrade           $http_upgrade;
            proxy_set_header   Connection        "upgrade";
            proxy_buffering    off;
            proxy_cache        off;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            add_header         X-Accel-Buffering no;
        }

'''

if OLD_CAMERA_BLOCK:
    nginx = nginx[:OLD_CAMERA_BLOCK.start()] + CAMERA_BLOCK_CORRECT + nginx[OLD_CAMERA_BLOCK.end():]
    print('[OK] Camera block diganti dengan versi correct')
else:
    # Sisipkan sebelum location /api/
    nginx = nginx.replace(
        '        location /api/ {',
        CAMERA_BLOCK_CORRECT + '        location /api/ {',
        1
    )
    print('[OK] Camera block disisipkan sebelum /api/')

# Upload
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(nginx.encode()), '/home/telur/tetasco-connect/nginx/nginx.conf')
sftp.close()
print('[OK] nginx.conf uploaded')

# Reload nginx (tidak perlu rebuild image)
r('docker exec tetasco-nginx nginx -s reload 2>&1 || docker compose -f ~/tetasco-connect/docker-compose.yml restart nginx',
  '1. Reload nginx', timeout=15)
time.sleep(5)

# Test WS endpoint dari lokal
r('curl -s -I -H "Upgrade: websocket" -H "Connection: upgrade" "http://localhost:8000/api/tetasco/1/camera/push" 2>/dev/null | head -3',
  '2. Test WS endpoint di backend')
r('curl -s "http://localhost:8000/api/tetasco/1/camera/stats"', '3. Camera stats')

# Restart Raspi (perlu SSH terpisah)
print('\n[INFO] Sekarang restart Raspi backend untuk reconnect WS...')
sv.close()

# Raspi
rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def rr(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

rr('pkill -9 -f "backend/app.py" 2>/dev/null; echo ok', '4. Kill Raspi backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(15)
rr('grep -E "CamPush|Connected|terhubung|Error|404|401" /tmp/tetasco_backend.log | tail -8', '5. CamPush log')

rs.close()
print('\n✅ Done! Cek stream di: https://tetasco.my.id/api/tetasco/1/camera/stream')
