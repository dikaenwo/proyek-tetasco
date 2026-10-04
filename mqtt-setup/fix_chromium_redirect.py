"""fix_chromium_redirect.py — Ganti subprocess.Popen dengan xdotool untuk navigate Chromium existing"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    s = (out or err).strip()
    sys.stdout.write(s + '\n' if s else '(kosong)\n'); sys.stdout.flush()
    return out

# 1. Install xdotool jika belum ada
r(rs, 'which xdotool || sudo apt-get install -y xdotool 2>&1 | tail -3', '1. xdotool check/install')

# 2. Buat script helper untuk redirect Chromium
REDIRECT_SCRIPT = '''#!/bin/bash
# redirect_chromium.sh — Navigate Chromium ke URL tertentu via xdotool
URL="${1:-http://127.0.0.1:5001/pair}"
export DISPLAY=:0

# Coba xdotool dulu (navigate existing Chromium)
WIN_ID=$(xdotool search --onlyvisible --class "Chromium" 2>/dev/null | head -1)
if [ -n "$WIN_ID" ]; then
    # Fokus window, buka address bar, ketik URL, enter
    xdotool windowactivate --sync "$WIN_ID"
    sleep 0.2
    xdotool key --window "$WIN_ID" ctrl+l
    sleep 0.3
    xdotool type --clearmodifiers --window "$WIN_ID" "$URL"
    sleep 0.2
    xdotool key --window "$WIN_ID" Return
    echo "[redirect_chromium] Navigated existing Chromium to $URL"
else
    # Tidak ada Chromium, buka baru
    pkill -f chromium 2>/dev/null; sleep 1
    chromium \\
        --start-fullscreen --noerrdialogs --disable-infobars \\
        --no-first-run --fast --fast-start --disable-translate \\
        --disable-pinch --overscroll-history-navigation=0 \\
        --touch-events=enabled "$URL" &
    echo "[redirect_chromium] Opened new Chromium to $URL"
fi
'''

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(REDIRECT_SCRIPT.encode()), '/home/tetasco1/redirect_chromium.sh')
sftp.close()
r(rs, 'chmod +x ~/redirect_chromium.sh && echo "✓ Script installed"', '2. Install redirect script')

# 3. Update app.py — ganti subprocess.Popen dengan panggil script
i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

OLD_SP = '''                # Paksa Chromium kembali ke halaman pairing
                _sp.Popen(
                    'DISPLAY=:0 pkill -f chromium; sleep 1; '
                    'DISPLAY=:0 chromium '
                    '--start-fullscreen --noerrdialogs --disable-infobars '
                    '--no-first-run --fast --fast-start --disable-translate '
                    '--disable-pinch --overscroll-history-navigation=0 '
                    '--touch-events=enabled '
                    'http://127.0.0.1:5001/pair &',
                    shell=True
                )'''

NEW_SP = '''                # Paksa Chromium kembali ke halaman pairing
                # Gunakan script helper yang support xdotool (navigate existing window)
                _sp.Popen(
                    'bash /home/tetasco1/redirect_chromium.sh http://127.0.0.1:5001/pair '
                    '>> /tmp/chromium_redirect.log 2>&1 &',
                    shell=True, env={**__import__("os").environ, "DISPLAY": ":0"}
                )'''

if OLD_SP in content:
    content = content.replace(OLD_SP, NEW_SP, 1)
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] app.py patched — pakai redirect_chromium.sh', flush=True)
else:
    print('[WARN] Pattern tidak ditemukan', flush=True)
    r(rs, 'grep -n "Popen\\|pkill.*chromium" ~/Penetas-Telur/backend/app.py | tail -10', 'Cek Popen')

# 4. Restart backend
r(rs, 'pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '3. Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
time.sleep(4)
r(rs, 'curl -s http://localhost:5001/api/health 2>/dev/null || curl -s http://localhost:5001/api/sensor | head -c 50',
  '4. Backend health')

# 5. Test xdotool langsung — cari window Chromium dan navigate ke /pair
r(rs, 'DISPLAY=:0 xdotool search --onlyvisible --class "Chromium" 2>/dev/null || echo "No chromium window found"',
  '5. Chromium window ID')

# 6. Coba redirect manual
r(rs, 'bash ~/redirect_chromium.sh http://127.0.0.1:5001/pair', '6. Test redirect manual → /pair')
time.sleep(3)
r(rs, 'cat /tmp/chromium_redirect.log 2>/dev/null || echo "log kosong"', '7. Redirect log')

rs.close()
print('\n✅ Done! LCD seharusnya buka /pair sekarang.', flush=True)
print('   Saat HP hapus lemari → watcher 30 detik → redirect otomatis', flush=True)
