import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# ── Diagnosis delay ──────────────────────────────────────

# 1. Cek Flask Raspi: single-thread atau multi-thread?
ras("grep -n 'threaded\\|app.run\\|debug\\|use_reloader\\|workers' ~/Penetas-Telur/backend/app.py | head -10", 'Flask run mode')

# 2. Ukur waktu respons Raspi dari server
print('\n=== Ukur waktu Raspi response ===')
for _ in range(3):
    t0 = time.time()
    srv("curl -s -o /dev/null -w '%{time_total}' -X POST http://192.168.1.27:5001/api/actuators/fan -H 'Content-Type: application/json' -d '{\"state\": true}'", 'Raspi response time')
    time.sleep(0.5)

# 3. Cek cloud_sync.push_device_state - apakah blocking?
ras("grep -n -A 10 'def push_device_state' ~/Penetas-Telur/backend/hardware/cloud_sync.py", 'push_device_state code')

# 4. Cek Raspi set_actuator (apakah push_device_state blocking di sana?)
ras("grep -n -B2 -A 5 'push_device_state' ~/Penetas-Telur/backend/app.py", 'push_device_state in set_actuator')

# 5. Cek apakah Flask threaded
ras("tail -20 ~/Penetas-Telur/backend/app.py", 'Flask main block')

rp.close()
sv.close()
