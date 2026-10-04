import paramiko, sys, io, time, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# 1. Stop cloudflared process
r('pkill -f cloudflared 2>/dev/null && echo "killed" || echo "sudah tidak jalan"', '1. Kill cloudflared process')

# 2. Disable dan hapus systemd service
r('sudo systemctl disable cloudflared-tetasco 2>/dev/null && echo "disabled" || echo "service tidak ada"', '2. Disable systemd service')
r('sudo rm -f /etc/systemd/system/cloudflared-tetasco.service && sudo systemctl daemon-reload && echo "deleted" || echo "tidak ada"', '3. Hapus service file')

# 3. Hapus binary cloudflared
r('rm -f ~/.local/bin/cloudflared && echo "deleted" || echo "tidak ada"', '4. Hapus cloudflared binary')
r('ls ~/.local/bin/ 2>/dev/null || echo "(kosong)"', '5. ~/.local/bin setelah bersih')

# 4. Bersihkan app.py dari kode tunnel (watcher thread + endpoint)
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')

# Hapus blok tunnel watcher
TUNNEL_SECTIONS = [
    # _watch_tunnel_log thread
    (r'def _watch_tunnel_log\(\):.*?_tw\.start\(\)\n', re.DOTALL),
    # _tunnel_url variable + inisialisasi
    (r'_tunnel_url\s*=\s*None.*?# Diisi oleh cloudflared watcher\n', 0),
    # /api/tunnel-url endpoint
    (r'@app\.route\(\'/api/tunnel-url\'\).*?return jsonify\(\{\'url\': None.*?\}\)\n\n', re.DOTALL),
]

original_len = len(app_py)
for pattern, flags in TUNNEL_SECTIONS:
    app_py = re.sub(pattern, '', app_py, flags=flags)

removed = original_len - len(app_py)
print(f'\n[6. Bersihkan app.py] Dihapus {removed} chars tunnel code')

# Upload app.py yang sudah bersih
sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py uploaded')

# 5. Restart backend
r('pkill -9 -f "backend/app.py" 2>/dev/null; echo ok', '7. Kill backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)
r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;print(json.load(sys.stdin)[\'status\'])"', '8. Backend health')
r('grep -E "CamPush|Terhubung|cloudflare|tunnel" /tmp/tetasco_backend.log | tail -5', '9. Log check')

rs.close()
print('\n✅ Cloudflared di Raspi lemari sudah BERSIH. WS push ke server tetap jalan.')
