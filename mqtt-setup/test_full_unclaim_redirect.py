"""test_full_unclaim_redirect.py — Test lengkap: set claimed → start chromium → unclaim → tunggu redirect"""
import paramiko, sys, time, requests
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

SERVER = 'https://tetasco.my.id'

# 1. Set status claimed di Raspi
r(rs, 'echo \'{"farm_name":"Kandang Live Test"}\' > ~/.tetasco_claimed && echo "✓ Flag claimed set"', '1. Set claimed flag')

# 2. Cek backend jalan
r(rs, 'curl -s http://localhost:5001/api/claim-status', '2. claim-status (harus true)')

# 3. Start Chromium ke dashboard (simulasi sudah paired, lihat dashboard)
print('\n[3. Start Chromium ke dashboard...]', flush=True)
rs.exec_command(
    'DISPLAY=:0 pkill -f chromium 2>/dev/null; sleep 1; '
    'DISPLAY=:0 chromium '
    '--start-fullscreen --noerrdialogs --disable-infobars '
    '--no-first-run --fast --fast-start --disable-translate '
    '--disable-pinch --overscroll-history-navigation=0 '
    '--touch-events=enabled '
    'http://127.0.0.1:5001/ &'
)
time.sleep(4)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '4. Chromium running (dashboard)?')

# 4. Unclaim di server (simulasi HP hapus lemari)
print('\n[5. HP hapus lemari → unclaim di server...]', flush=True)
tok = requests.get(f'{SERVER}/api/tetasco/1/claim-token', timeout=10).json()['token']
requests.post(f'{SERVER}/api/claim', json={
    'tetascoId': 1, 'claimToken': tok,
    'appId': 'live-test-001', 'farmName': 'Kandang Live Test'
}, timeout=10)
time.sleep(1)
requests.delete(f'{SERVER}/api/claim/1?appId=live-test-001', timeout=5)
print('  → Server: lemari unclaimed ✓', flush=True)
r(rs, 'curl -s https://tetasco.my.id/api/tetasco/1/is-claimed', '6. Server is-claimed (harus false)')

# 5. Tunggu watcher detect (watcher interval 30 detik)
print('\n[7. Tunggu watcher detect unclaim (35 detik)...]', flush=True)
for i in range(7):
    sys.stdout.write(f'  {(i+1)*5}s...'); sys.stdout.flush()
    time.sleep(5)
print(' → Selesai!', flush=True)

# 6. Cek hasil
r(rs, 'ls -la ~/.tetasco_claimed 2>/dev/null || echo "✓ Flag TERHAPUS! Watcher berhasil!"', '8. Flag file status')
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '9. Chromium procs (setelah watcher)')
r(rs, 'grep "Unclaim Watcher\|chromium\|/pair" /tmp/tetasco_backend.log | tail -10', '10. Watcher log')

# 7. Cleanup
r(rs, 'rm -f ~/.tetasco_claimed', 'Cleanup')
rs.close()
print('\n✅ Test selesai!', flush=True)
