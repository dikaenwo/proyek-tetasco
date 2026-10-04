import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Test dari dalam container pakai Python
print('=== Test koneksi dari container ke Raspi ===')
result = srv(
    """docker exec tetasco-backend python3 -c "
import urllib.request, json
try:
    r = urllib.request.urlopen('http://192.168.1.27:5001/api/actuators', timeout=3)
    print('OK:', r.read().decode()[:80])
except Exception as e:
    print('ERROR:', e)
" 2>&1""",
    'Container Python → Raspi'
)

# Kalau gagal, cek apakah Flask Raspi bind ke 0.0.0.0
ras('ss -tlnp | grep 5001', 'Raspi bind address')
ras('pgrep -fa python3', 'Raspi processes')

# Cek apakah ada proses baru yang crash dan lama yang jalan
ras('tail -5 /tmp/tetasco_backend.log', 'Raspi log')

# Kalau Flask hanya bind ke 127.0.0.1, fix itu
ras("grep 'app.run' ~/Penetas-Telur/backend/app.py", 'app.run config')

# Test timeout dari server host (bukan container)
print('\n=== Ukur timing dari host (bukan container) ===')
for action in ['on', 'off', 'on']:
    t0 = time.time()
    srv(f"curl -s -X POST http://192.168.1.27:5001/api/actuators/fan -H 'Content-Type: application/json' -d '{{\"state\": {\"true\" if action==\"on\" else \"false\"}}}'", f'Host curl fan {action}')
    print(f'  Host→Raspi time: {(time.time()-t0)*1000:.0f}ms')

rp.close()
sv.close()
