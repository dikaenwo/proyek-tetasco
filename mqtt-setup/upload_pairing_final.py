"""upload_pairing_final.py — Upload pairing.html terbaru ke Raspi + final test"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# 1. Upload pairing.html terbaru
with open('raspberry_pi/pairing.html', 'rb') as f:
    sftp = rs.open_sftp()
    sftp.putfo(f, '/home/tetasco1/Penetas-Telur/pairing.html')
    sftp.close()
print('[OK] pairing.html uploaded (v2 — auto-redirect if claimed)', flush=True)

# 2. Test semua endpoint lokal
r(rs, 'curl -s http://localhost:5001/api/pairing-info', '1. pairing-info')
r(rs, 'curl -s http://localhost:5001/api/claim-status', '2. claim-status (belum claimed)')

# 3. Simulasi claim dari server pusat → Raspi harus detect
r(rs, f'curl -s -X POST http://localhost:5001/api/mark-claimed -H "Content-Type: application/json" -d \'{{"farmName":"Kandang Utama","appId":"test-app-001"}}\'',
  '3. Simulasi mark-claimed')

r(rs, 'curl -s http://localhost:5001/api/claim-status', '4. claim-status (setelah claimed)')

# 4. Reset flag untuk demo clean
r(rs, 'rm -f ~/.tetasco_claimed && echo "Flag dihapus (reset)"', '5. Reset claimed flag')
r(rs, 'curl -s http://localhost:5001/api/claim-status', '6. claim-status (setelah reset)')

# 5. Test /pair page headers
r(rs, 'curl -si http://localhost:5001/pair 2>&1 | head -6', '7. /pair endpoint')

# 6. Reload Chromium ke /pair
r(rs, 'pkill -f chromium 2>/dev/null; sleep 1; echo "Chromium killed"', '8. Kill Chromium')
time.sleep(1)
rs.exec_command(
    'DISPLAY=:0 chromium '
    '--start-fullscreen --noerrdialogs --disable-infobars '
    '--no-first-run --fast --fast-start --disable-translate '
    '--disable-pinch --overscroll-history-navigation=0 '
    '--touch-events=enabled '
    '--window-size=1024,600 --window-position=0,0 '
    'http://127.0.0.1:5001/pair &'
)
time.sleep(3)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '9. Chromium running?')

rs.close()
print('\n✅ Pairing page siap! Monitor HDMI sekarang tampilkan welcome screen.', flush=True)
print('   Buka http://192.168.1.27:5001/pair dari browser untuk preview', flush=True)
