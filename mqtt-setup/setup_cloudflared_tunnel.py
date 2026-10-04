"""setup_cloudflared_tunnel.py — Install cloudflared + buat tunnel permanen di Raspi"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=60):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# 1. Deteksi arsitektur
arch = r('uname -m', '1. Arsitektur')
if 'aarch64' in arch:
    pkg = 'cloudflared-linux-arm64'
elif 'armv' in arch:
    pkg = 'cloudflared-linux-arm'
else:
    pkg = 'cloudflared-linux-amd64'
print(f'   Paket: {pkg}')

# 2. Download cloudflared
r(f'curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/{pkg}" -o /tmp/cloudflared && chmod +x /tmp/cloudflared && mv /tmp/cloudflared /usr/local/bin/cloudflared && echo "OK"',
  '2. Download cloudflared', timeout=120)

# 3. Verifikasi
r('cloudflared --version', '3. Versi cloudflared')

# 4. Jalankan quick tunnel (no login required) di background
# Ini buat tunnel sementara — untuk permanen perlu login Cloudflare
print('\n[4. Start quick tunnel ke port 5001...]', flush=True)
rs.exec_command('pkill -f "cloudflared tunnel" 2>/dev/null || true')
time.sleep(1)
rs.exec_command(
    'nohup cloudflared tunnel --url http://localhost:5001 > /tmp/cloudflared.log 2>&1 &'
)
time.sleep(12)  # Tunggu tunnel establish

# 5. Ambil URL tunnel
tunnel_log = r('cat /tmp/cloudflared.log', '5. Tunnel log')

# Cari URL https://xxx.trycloudflare.com
import re
urls = re.findall(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', tunnel_log)
if urls:
    tunnel_url = urls[0]
    print(f'\n✅ TUNNEL URL: {tunnel_url}')
    print(f'   Stream:     {tunnel_url}/api/camera/stream')
    print(f'   Viewer:     {tunnel_url}/camera')
    print(f'   Dashboard:  {tunnel_url}/')
else:
    print('[WARN] URL belum muncul, cek log:')
    print(tunnel_log[-800:])

# 6. Buat service systemd agar tunnel auto-start saat boot
SERVICE = """[Unit]
Description=Cloudflare Quick Tunnel for Tetasco
After=network.target tetasco-backend.service

[Service]
Type=simple
User=tetasco1
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:5001
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
sftp = rs.open_sftp()
import io
sftp.putfo(io.BytesIO(SERVICE.encode()), '/tmp/cloudflared-tetasco.service')
sftp.close()
r('sudo cp /tmp/cloudflared-tetasco.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable cloudflared-tetasco && echo "Service enabled"',
  '6. Install systemd service', timeout=30)

rs.close()
