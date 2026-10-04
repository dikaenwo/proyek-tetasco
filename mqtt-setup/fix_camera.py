import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# ── Fix 1: Raspi — ubah urutan video device (video0 dulu) ────────────────────
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

OLD_ORDER = "    for dev in ['/dev/video1', '/dev/video0', '/dev/video2']:"
NEW_ORDER = "    for dev in ['/dev/video0', '/dev/video1', '/dev/video2']:  # video0 = UVC capture, video1 = metadata"

if OLD_ORDER in app:
    app = app.replace(OLD_ORDER, NEW_ORDER, 1)
    print('[OK] Urutan device diperbaiki: video0 dulu')
else:
    print('[WARN] Urutan device tidak ditemukan, cek...')
    import re
    m = re.search(r'for dev in \[.*?video.*?\]', app)
    if m: print('[DEBUG]', m.group())

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo OK', 'Syntax check')

# ── Check server camera endpoint ─────────────────────────────────────────────
srv('docker logs tetasco-backend --tail 20 2>&1 | grep -i "camera\|ws\|websocket\|502\|push" | tail -10', 'Server camera logs')
srv('docker exec tetasco-backend grep -n "camera\|push\|websocket" /app/main.py | head -15', 'Server camera endpoints')

# Cek nginx/cloudflare WebSocket config
srv('cat /home/telur/tetasco-connect/nginx.conf 2>/dev/null | grep -A5 "camera\|ws\|upgrade" | head -20', 'Nginx WS config')

# Restart Raspi backend dengan fix
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('\n[OK] Raspi restart')
time.sleep(10)

ras('tail -15 /tmp/tetasco_backend.log | grep -i "camera\|video\|cam\|push\|error" ', 'Camera log setelah restart')

rp.close()
sv.close()
