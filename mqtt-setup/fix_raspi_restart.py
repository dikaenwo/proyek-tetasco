import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')
    return out

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Cek apa yang terjadi
ras('pgrep -fa python3', 'Python proses aktif')
ras('ss -tlnp | grep 5001 || echo "port 5001 tidak ada"', 'Port 5001')
ras('tail -20 /tmp/tetasco_backend.log 2>/dev/null || echo "no log"', 'App log')

# Cek error di app.py (mungkin ada syntax error dari patch cloud_sync)
ras('cd ~/Penetas-Telur && python3 -c "import backend.hardware.cloud_sync" 2>&1', 'Cek import cloud_sync')
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/cloud_sync.py 2>&1 && echo OK', 'Syntax check cloud_sync')
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py 2>&1 && echo OK', 'Syntax check app.py')

# Jika syntax OK, restart
print('\nStart app.py...')
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(3)
chan.close()

time.sleep(5)
ras('pgrep -fa "python3 backend/app.py" | grep -v pgrep | head -2', 'Proses baru')
ras('ss -tlnp | grep 5001 || echo "port 5001 tidak open"', 'Port 5001 cek')
ras('tail -10 /tmp/tetasco_backend.log', 'App log sekarang')

# Test koneksi dari server
time.sleep(5)
srv("curl -s http://192.168.1.27:5001/api/actuators 2>&1 | head -c 100", 'Test Raspi dari server')

# Test end-to-end timing
print('\n=== TIMING TEST ===')
import time as _t
for label, action in [('Fan ON','on'), ('Fan OFF','off'), ('Fan ON lagi','on')]:
    t0 = _t.time()
    r = srv(f"curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/{action}", label)
    t1 = _t.time()
    print(f'  {(t1-t0)*1000:.0f}ms')

srv('docker logs tetasco-backend --tail 5 2>&1 | grep -i "DirectFwd"', 'DirectFwd status')

rp.close()
sv.close()
print('\nDone!')
