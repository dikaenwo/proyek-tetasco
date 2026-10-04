"""final_check_actuators.py — Tunggu 40 detik lalu verifikasi actuators + sensor_status"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Cek kode sensor_status di main.py
r(cs, 'grep -n "sensor_status" /home/telur/tetasco-connect/backend/main.py', '1. Kode sensor_status di main.py')

# Tunggu 40 detik untuk heartbeat lemari-1
print('\n[Tunggu 40 detik untuk heartbeat (t=5s+30s)...]\n', flush=True)
time.sleep(40)

# Final check semua endpoint
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '2. Sensor endpoint (dengan actuators)')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/status | python3 -m json.tool', '3. Status endpoint')
r(cs, 'docker logs tetasco-backend --since=1m 2>&1 | grep -iE "Status|Sensor|lemari" | tail -8', '4. Server logs')

cs.close()
print('\n✅ Done!', flush=True)
