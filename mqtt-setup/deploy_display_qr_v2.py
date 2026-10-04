"""deploy_display_qr_v2.py — Upload display_qr.py ke Raspi dengan fix pip dan sudo"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RASPI_HOST = '192.168.1.27'
RASPI_USER = 'tetasco1'
RASPI_PASS = 'saumata1192'
TETASCO_ID = 1

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect(RASPI_HOST, 22, RASPI_USER, RASPI_PASS, timeout=15)

def r(c, cmd, lbl='', timeout=120):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    if out: sys.stdout.write(out); sys.stdout.flush()
    if err and 'warning' not in err.lower(): sys.stdout.write(err); sys.stdout.flush()
    return out

def sudo_r(c, cmd, lbl='', timeout=60):
    """Jalankan command dengan sudo -S (kirim password via stdin)"""
    if lbl: print(f'\n[{lbl}]', flush=True)
    full_cmd = f'echo "{RASPI_PASS}" | sudo -S {cmd} 2>&1'
    i, o, e = c.exec_command(full_cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    sys.stdout.write(out); sys.stdout.flush()
    return out

# 1. Install via apt (lebih stabil dari pip di Bookworm)
print('\n[1. Install packages via apt]', flush=True)
sudo_r(rs, 'apt-get install -y python3-qrcode python3-pygame python3-requests python3-pil python3-pillow 2>&1 | tail -5')

# Fallback pip dengan --break-system-packages
r(rs, 'pip3 install qrcode[pil] pillow pygame requests --break-system-packages 2>&1 | grep -E "Successfully|already|error" | head -5',
  '1b. Pip fallback (break-system-packages)')

# 2. Upload script
with open('raspberry_pi/display_qr.py', 'rb') as f:
    sftp = rs.open_sftp()
    sftp.putfo(f, f'/home/{RASPI_USER}/display_qr.py')
    sftp.close()
print(f'[OK] display_qr.py uploaded', flush=True)
r(rs, f'chmod +x /home/{RASPI_USER}/display_qr.py')

# 3. Test headless (tanpa display)
r(rs, f'TETASCO_ID={TETASCO_ID} TETASCO_SERVER=https://tetasco.my.id '
      f'SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy '
      f'timeout 8 python3 /home/{RASPI_USER}/display_qr.py 2>&1 | head -20',
  '2. Test headless (8 detik)')

# 4. Buat systemd service via sudo -S
SERVICE = f"""[Unit]
Description=Tetasco QR Display Lemari {TETASCO_ID}
After=network-online.target graphical-session.target
Wants=network-online.target

[Service]
Type=simple
User={RASPI_USER}
Environment=TETASCO_ID={TETASCO_ID}
Environment=TETASCO_SERVER=https://tetasco.my.id
Environment=TETASCO_NAME=Lemari #{TETASCO_ID}
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/{RASPI_USER}/.Xauthority
Environment=SDL_VIDEODRIVER=x11
ExecStartPre=/bin/sleep 15
ExecStart=/usr/bin/python3 /home/{RASPI_USER}/display_qr.py
Restart=on-failure
RestartSec=15

[Install]
WantedBy=graphical.target
"""

# Tulis service file
sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(SERVICE.encode()), f'/home/{RASPI_USER}/tetasco-display.service')
sftp.close()

sudo_r(rs, f'cp /home/{RASPI_USER}/tetasco-display.service /etc/systemd/system/tetasco-display.service',
       '3. Copy service file')
sudo_r(rs, 'systemctl daemon-reload && systemctl enable tetasco-display.service && echo "Service enabled"',
       '4. Enable service')

# 5. Cek X display tersedia
r(rs, 'echo $DISPLAY; ls ~/.Xauthority 2>/dev/null || echo "Xauth tidak ada"', '5. Cek X display')

# 6. Coba jalankan manual (dengan DISPLAY=:0 jika ada)
r(rs, f'TETASCO_ID={TETASCO_ID} TETASCO_SERVER=https://tetasco.my.id '
      f'DISPLAY=:0 XAUTHORITY=/home/{RASPI_USER}/.Xauthority '
      f'timeout 5 python3 /home/{RASPI_USER}/display_qr.py &',
  '6. Start QR display (background)')

time.sleep(3)
r(rs, 'ps aux | grep display_qr | grep -v grep', '7. Process check')

rs.close()
print('\n✅ Done!', flush=True)
print(f'Untuk start manual: ssh {RASPI_USER}@{RASPI_HOST} "DISPLAY=:0 python3 ~/display_qr.py"')
