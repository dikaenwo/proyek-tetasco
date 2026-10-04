"""debug_raspi_poll.py — Debug kenapa Raspi tidak detect klaim dari server"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Test apakah Raspi bisa akses tetasco.my.id via HTTPS
r(rs, 'curl -sv https://tetasco.my.id/api/health 2>&1 | tail -5', '1. HTTPS curl ke server pusat')
r(rs, 'curl -s https://tetasco.my.id/api/tetasco/1/is-claimed', '2. is-claimed dari Raspi')

# Test Python urllib
r(rs, '''python3 -c "
import urllib.request, ssl, json
ctx = ssl.create_default_context()
try:
    with urllib.request.urlopen('https://tetasco.my.id/api/tetasco/1/is-claimed', context=ctx, timeout=10) as r:
        print('OK:', json.loads(r.read().decode()))
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
"''', '3. Python urllib test')

# Cek claim-status fungsi saat ini
r(rs, 'grep -A 30 "def api_claim_status" ~/Penetas-Telur/backend/app.py | head -35', '4. Fungsi claim-status saat ini')

# Cek log backend untuk error
r(rs, 'tail -20 /tmp/tetasco_backend.log', '5. Backend log')

# App.py size check (apakah ada duplikasi?)
r(rs, 'wc -l ~/Penetas-Telur/backend/app.py', '6. Ukuran app.py')
r(rs, 'grep -c "claim-status" ~/Penetas-Telur/backend/app.py', '7. Berapa kali claim-status muncul')

rs.close()
print('\nDone!', flush=True)
