import paramiko, sys, io, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    return o.read().decode('utf-8','replace').strip()

# Stop motor dulu
print('[STOP]', ras('curl -s -X POST http://localhost:5001/api/hydraulic/command -H "Content-Type: application/json" -d \'{"action":"stop"}\'')[:60])
time.sleep(1)

# Patch app.py: t_center_to_edge default 3.4 → 3.0
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')
app = app.replace("float(data.get('t_center_to_edge', 3.4))", "float(data.get('t_center_to_edge', 3.0))")
print('[Patch] t_center_to_edge=3.0:', "3.0" in app and "t_center_to_edge', 3.0" in app)

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Raspi restart')
time.sleep(7)

# Test
raw = ras('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d "{}"')
try:
    d = json.loads(raw)
    print(f'[OK] t_edge={d["t_center_to_edge"]}s  t_full={d["t_full"]}s  total={d["total_duration_sec"]}s')
    print(f'     state={d["state"]}  is_oscillating={d["is_oscillating"]}')
except:
    print('[RAW]', raw[:200])

rp.close()
print('\nSelesai! Motor sedang mulai sequence dengan t_edge=3.0s')
