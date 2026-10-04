"""fix_wayland_redirect.py — Fix redirect script + app.py watcher dengan Wayland env vars"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# 1. Update redirect_chromium.sh dengan Wayland env vars yang benar
REDIRECT_SCRIPT = '''#!/bin/bash
# redirect_chromium.sh — Navigate Chromium ke URL via kill+restart (Wayland safe)
URL="${1:-http://127.0.0.1:5001/pair}"

# Set env vars untuk Wayland + XWayland
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000

CHROMIUM_BIN="/usr/bin/chromium"
if ! [ -f "$CHROMIUM_BIN" ]; then
    CHROMIUM_BIN=$(which chromium-browser chromium 2>/dev/null | head -1)
fi

echo "[redirect_chromium] $(date) → $URL"

# Matikan Chromium yang ada
pkill -f "$CHROMIUM_BIN" 2>/dev/null
sleep 2

# Buka Chromium ke URL baru
$CHROMIUM_BIN \\
    --start-fullscreen \\
    --noerrdialogs \\
    --disable-infobars \\
    --no-first-run \\
    --fast \\
    --fast-start \\
    --disable-translate \\
    --disable-pinch \\
    --overscroll-history-navigation=0 \\
    --touch-events=enabled \\
    --window-size=1024,600 \\
    --window-position=0,0 \\
    "$URL" &

echo "[redirect_chromium] Chromium started at $URL (PID: $!)"
'''

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(REDIRECT_SCRIPT.encode()), '/home/tetasco1/redirect_chromium.sh')
sftp.close()
r(rs, 'chmod +x ~/redirect_chromium.sh && echo "✓ redirect_chromium.sh updated"', '1. Update redirect script')

# 2. Update app.py watcher untuk pakai env vars Wayland
i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

OLD_POPEN = (
    '                # Paksa Chromium kembali ke halaman pairing\n'
    '                # Gunakan script helper yang support xdotool (navigate existing window)\n'
    '                _sp.Popen(\n'
    '                    \'bash /home/tetasco1/redirect_chromium.sh http://127.0.0.1:5001/pair \'\n'
    '                    \'>> /tmp/chromium_redirect.log 2>&1 &\',\n'
    '                    shell=True, env={**__import__("os").environ, "DISPLAY": ":0"}\n'
    '                )'
)

NEW_POPEN = (
    '                # Paksa Chromium kembali ke halaman pairing (Wayland-safe)\n'
    '                _wayland_env = {\n'
    '                    **__import__("os").environ,\n'
    '                    "DISPLAY": ":0",\n'
    '                    "WAYLAND_DISPLAY": "wayland-0",\n'
    '                    "XDG_RUNTIME_DIR": "/run/user/1000",\n'
    '                }\n'
    '                _sp.Popen(\n'
    '                    \'bash /home/tetasco1/redirect_chromium.sh http://127.0.0.1:5001/pair \'\n'
    '                    \'>> /tmp/chromium_redirect.log 2>&1\',\n'
    '                    shell=True, env=_wayland_env\n'
    '                )'
)

if OLD_POPEN in content:
    content = content.replace(OLD_POPEN, NEW_POPEN, 1)
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] app.py updated — watcher pakai Wayland env vars', flush=True)
else:
    print('[WARN] Pattern tidak ditemukan! Cek manual:', flush=True)
    r(rs, 'grep -n "redirect_chromium\|Popen\|WAYLAND" ~/Penetas-Telur/backend/app.py | tail -10', 'Cek Popen di app.py')

# 3. Restart backend
r(rs, 'pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '2. Kill backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(7)
r(rs, 'curl -s http://localhost:5001/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'✓ Backend OK:\', d[\'status\'])"',
  '3. Backend health')

# 4. Buka Chromium ke dashboard (React SPA terbaru sudah ada watcher fix)
print('\n[4. Buka Chromium ke dashboard dengan env vars baru...]', flush=True)
rs.exec_command(
    'DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 '
    'pkill -f chromium 2>/dev/null; sleep 2; '
    'DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 '
    '/usr/bin/chromium '
    '--start-fullscreen --noerrdialogs --disable-infobars '
    '--no-first-run --fast --fast-start --disable-translate '
    '--disable-pinch --overscroll-history-navigation=0 '
    '--touch-events=enabled --window-size=1024,600 --window-position=0,0 '
    'http://127.0.0.1:5001 > /tmp/chromium_start.log 2>&1 &'
)
time.sleep(6)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '5. Chromium procs')
r(rs, 'cat /tmp/chromium_start.log 2>/dev/null | head -5', '6. Chromium start log')

# 5. Test redirect langsung ke /pair
print('\n[7. Test redirect ke /pair...]', flush=True)
rs.exec_command('bash ~/redirect_chromium.sh http://127.0.0.1:5001/pair >> /tmp/chromium_redirect.log 2>&1 &')
time.sleep(6)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '8. Chromium procs setelah redirect')
r(rs, 'cat /tmp/chromium_redirect.log 2>/dev/null', '9. Redirect log')

rs.close()
print('\n✅ Done! LCD seharusnya menampilkan halaman /pair (welcome screen)', flush=True)
