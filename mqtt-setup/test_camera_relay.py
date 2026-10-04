import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Restart Raspi backend
r('pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '1. Kill backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(12)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;print(json.load(sys.stdin)[\'status\'])"', '2. Backend health')
r('grep -E "CamPush|Connected|Error" /tmp/tetasco_backend.log | tail -8', '3. CamPush log')

rs.close()

# Test dari server side
import urllib.request
print('\n[4. Test camera stats dari luar (via Cloudflare)]')
try:
    req = urllib.request.urlopen('https://tetasco.my.id/api/tetasco/1/camera/stats', timeout=10)
    print(req.read().decode())
except Exception as e:
    print(f'Error: {e}')
    # Coba tanpa cloudflare (via local server)
    print('\n[4b. Test via localhost]')

print('\n✅ Done!')
print('Stream URL: https://tetasco.my.id/api/tetasco/1/camera/stream')
