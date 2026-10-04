import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=60):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Rebuild backend agar patch permanen
srv('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5', 'Rebuild backend', t=120)
srv('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -6', 'Docker up', t=30)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Final end-to-end test
time.sleep(10)
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor (harus realtime)')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/off", 'Fan OFF')

sv.close()
print('\n✅ Rebuild selesai!')
