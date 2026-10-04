"""restart_and_test.py — Restart backend + verify unclaim redirect"""
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

# 1. Cek apakah backend sudah jalan
r(rs, 'ps aux | grep "backend/app.py" | grep -v grep', '1. Backend running?')

# 2. Restart backend
r(rs, 'pkill -9 -f "backend/app.py" 2>/dev/null; echo killed_ok', '2. Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Backend started', flush=True)
time.sleep(6)

# 3. Cek backend log
r(rs, 'tail -6 /tmp/tetasco_backend.log', '3. Backend log')
r(rs, 'curl -s http://localhost:5001/api/claim-status', '4. claim-status')

# 4. Set claimed + test unclaim
r(rs, 'echo \'{"farm_name":"Kandang Test"}\' > ~/.tetasco_claimed && echo "flag set"', '5. Set claimed flag')
r(rs, 'curl -s http://localhost:5001/api/claim-status', '6. Status (claimed)')

# 5. Unclaim via server pusat (simualsi HP hapus)
print('\n[7. Unclaim via server pusat (simulasi HP hapus)...]', flush=True)
SERVER = 'https://tetasco.my.id'
tok = requests.get(f'{SERVER}/api/tetasco/1/claim-token', timeout=10).json()['token']
requests.post(f'{SERVER}/api/claim', json={
    'tetascoId': 1, 'claimToken': tok,
    'appId': 'restart-test-001', 'farmName': 'Test Restart'
}, timeout=10)
print('  → Claimed di server', flush=True)
time.sleep(2)

# Sekarang delete/unclaim dari server (simulasi HP hapus)
requests.delete(f'{SERVER}/api/claim/1?appId=restart-test-001', timeout=5)
print('  → Unclaimed dari server', flush=True)

# 6. Cek is-claimed langsung
r(rs, 'curl -s https://tetasco.my.id/api/tetasco/1/is-claimed', '8. Server is-claimed')

# 7. Cek claim-status di Raspi (harus poll server dan detect unclaim)
r(rs, 'curl -s http://localhost:5001/api/claim-status', '9. Raspi claim-status')

# 8. Cek apakah watcher thread sudah berjalan
r(rs, 'grep -n "_unclaim_watcher\\|chromium\\|Chromium" /tmp/tetasco_backend.log | tail -10', '10. Log watcher')

# 9. Cek chromium processes
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', '11. Chromium procs')

# Cleanup
r(rs, 'rm -f ~/.tetasco_claimed && echo "cleaned"', '12. Cleanup')
rs.close()
print('\n✅ Done!', flush=True)
