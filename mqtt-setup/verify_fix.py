import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n[RASPI: {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER: {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# 1. Restart Raspi app.py
ras('pkill -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo killed', 'Kill old process')
ras('cd ~/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &; echo started', 'Start app.py')
time.sleep(8)
ras('pgrep -fa "python3 backend/app.py"', 'Process check')
ras('tail -10 /tmp/tetasco_backend.log', 'Log check')

# 2. Tunggu sensor push
print('\nTunggu 20 detik untuk sensor data push...')
time.sleep(20)

# 3. Cek sensor di server
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor data setelah 20 detik')
srv('curl -s http://localhost:8000/api/tetasco/1', 'GET tetasco/1')

# 4. Cek pending-commands endpoint di server - apakah patch berhasil?
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON command')
time.sleep(1)
srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands setelah fan ON')
srv('curl -s http://localhost:8000/api/tetasco/1', 'GET tetasco/1 setelah fan ON - check desired state')

rp.close()
sv.close()
