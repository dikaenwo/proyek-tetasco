import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca app.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Ganti URL push: ws://tetasco.my.id → ws://192.168.1.14 (LAN langsung, bypass Cloudflare)
OLD_URL = 'TETASCO_SERVER_WS = "ws://tetasco.my.id/api/tetasco/1/camera/push"'
NEW_URL = (
    '# LAN IP (bypass Cloudflare) — lebih cepat dan stabil untuk push dalam jaringan lokal\n'
    'TETASCO_SERVER_WS = "ws://192.168.1.14/api/tetasco/1/camera/push"'
)

if OLD_URL in app:
    app = app.replace(OLD_URL, NEW_URL, 1)
    print('[OK] URL push diubah ke LAN IP: ws://192.168.1.14/...')
else:
    print('[WARN] URL tidak ditemukan, cek...')
    import re
    m = re.search(r'TETASCO_SERVER_WS\s*=\s*"[^"]+"', app)
    if m: print('[DEBUG]', m.group())

# Tulis balik
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK', 'Syntax check')

# Test koneksi LAN ke server WebSocket dulu
ras('curl -s -o /dev/null -w "%{http_code}" http://192.168.1.14/api/health', 'LAN reach test')

# Restart Raspi backend
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart Raspi backend')
time.sleep(10)

# Cek log — apakah kamera berhasil connect
ras('tail -20 /tmp/tetasco_backend.log | grep -i "camera\|cam\|video\|push\|error\|connect"', 'Camera log setelah restart')

rp.close()
