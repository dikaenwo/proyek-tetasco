"""fix_backend_restart.py — Cek masalah restart backend + test akhir"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=25):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    s = out or err
    print(s if s else '(kosong)'); sys.stdout.flush()
    return out

# 1. Diagnosa
r(rs, 'ps aux | grep "app.py" | grep -v grep', '1. Backend process')
r(rs, 'netstat -tlnp 2>/dev/null | grep 5001 || ss -tlnp | grep 5001', '2. Port 5001')

# 2. Paksa kill + restart
r(rs, 'pkill -9 -f "app.py" 2>/dev/null; sleep 1; echo killed_all', '3. Kill ALL app.py')
time.sleep(2)

# Start via login shell agar env vars benar
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
print('[OK] Backend started via bash login shell', flush=True)
time.sleep(8)

# 3. Cek backend jalan
r(rs, 'ps aux | grep "backend/app.py" | grep -v grep | head -3', '4. Backend process (baru)')
r(rs, 'curl -s http://localhost:5001/api/health', '5. Health check')
r(rs, 'tail -8 /tmp/tetasco_backend.log', '6. Backend log')

# 4. Set Chromium buka /pair langsung (force reload)
r(rs, 'curl -s http://localhost:5001/api/claim-status', '7. Claim status')

# 5. Buka Chromium ke /pair
print('\n[8. Buka Chromium ke /pair...]', flush=True)
rs.exec_command(
    'export DISPLAY=:0 XAUTHORITY=/home/tetasco1/.Xauthority; '
    'pkill -f chromium 2>/dev/null; sleep 2; '
    'chromium-browser '
    '--kiosk --noerrdialogs --disable-infobars '
    '--no-first-run --fast --fast-start '
    '--app=http://127.0.0.1:5001/pair &'
)
time.sleep(5)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '9. Chromium procs')

# 6. Coba alternatif jika chromium-browser tidak ada
r(rs, 'which chromium chromium-browser 2>/dev/null', '10. Chromium binary path')

rs.close()
print('\n✅ Done!', flush=True)
