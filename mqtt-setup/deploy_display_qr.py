"""deploy_display_qr.py — Upload display_qr.py ke Raspi dan setup autostart via systemd"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RASPI_HOST = '192.168.1.27'   # ganti sesuai IP Raspi lemari-1
RASPI_USER = 'tetasco1'
RASPI_PASS = 'saumata1192'
TETASCO_ID = 1

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect(RASPI_HOST, 22, RASPI_USER, RASPI_PASS, timeout=15)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=60)
    out = o.read().decode('utf-8', 'replace')
    err = e.read().decode('utf-8', 'replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# ── 1. Install dependencies ──────────────────────────────────────────────────
r(rs, 'pip3 install qrcode[pil] pygame requests pillow 2>&1 | tail -5', '1. Install dependencies')

# ── 2. Upload display_qr.py ──────────────────────────────────────────────────
with open('raspberry_pi/display_qr.py', 'rb') as f:
    sftp = rs.open_sftp()
    sftp.putfo(f, f'/home/{RASPI_USER}/display_qr.py')
    sftp.close()
print('[OK] display_qr.py di-upload ke Raspi', flush=True)

r(rs, f'chmod +x /home/{RASPI_USER}/display_qr.py', '2. chmod')

# ── 3. Test run (background, 10 detik lalu kill) ──────────────────────────────
# Cek dulu apakah ada X display
r(rs, 'echo $DISPLAY; loginctl show-session $(loginctl|grep pi|awk\'{print $1}\') -p Display 2>/dev/null || echo "Cek display..."',
  '3. Cek X display')

# ── 4. Buat systemd service untuk autostart ───────────────────────────────────
SERVICE = f"""[Unit]
Description=Tetasco QR Display — Lemari {TETASCO_ID}
After=network-online.target graphical.target
Wants=network-online.target

[Service]
Type=simple
User={RASPI_USER}
Environment=TETASCO_ID={TETASCO_ID}
Environment=TETASCO_SERVER=https://tetasco.my.id
Environment=TETASCO_NAME=Lemari+#{TETASCO_ID}
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/{RASPI_USER}/.Xauthority
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 /home/{RASPI_USER}/display_qr.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target
"""

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(SERVICE.encode()), '/tmp/tetasco-display.service')
sftp.close()

r(rs, 'sudo cp /tmp/tetasco-display.service /etc/systemd/system/tetasco-display.service',
  '4. Install systemd service')
r(rs, 'sudo systemctl daemon-reload && sudo systemctl enable tetasco-display.service && echo "Service enabled"',
  '5. Enable autostart')

# ── 5. Test manual tanpa X display (terminal mode saja) ───────────────────────
print('\n[INFO] Test quick (tanpa display, 5 detik):', flush=True)
r(rs, f'TETASCO_ID={TETASCO_ID} TETASCO_SERVER=https://tetasco.my.id SDL_VIDEODRIVER=dummy '
      f'timeout 5 python3 /home/{RASPI_USER}/display_qr.py 2>&1 | head -20',
  '6. Quick test headless')

rs.close()
print('\n✅ Done! Reboot Raspi untuk autostart QR display.', flush=True)
print('Atau manual: DISPLAY=:0 python3 ~/display_qr.py', flush=True)
