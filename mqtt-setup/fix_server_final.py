"""fix_server_final.py — Fix server: sensor endpoint baca actuators dari status_cache (flat)"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

MAIN = '/home/telur/tetasco-connect/backend/main.py'

# Baca server main.py
i, o, e = cs.exec_command(f'cat {MAIN}')
content = o.read().decode('utf-8', 'replace')

# ── Fix sensor endpoint (get_device_sensor) ──────────────────────────────────
# Ubah: data.get("actuators", {}) → bangun dari status_cache (flat, tanpa ts/device_id)
META_KEYS = '{"ts", "device_id"}'
old1 = '"actuators":    device_status_cache.get(device_id, {}).get("actuators", {}),'
new1 = f'"actuators":    {{k: v for k, v in device_status_cache.get(device_id, {{}}).items() if k not in {META_KEYS}}},'

count1 = content.count(old1)
content = content.replace(old1, new1)
print(f'[OK] Fix sensor endpoint actuators ({count1} occurrences)', flush=True)

# ── Fix status endpoint (get_device_status) ──────────────────────────────────
# Ubah: "actuators": status → flat dict tanpa ts/device_id
old2 = '"actuators":   status.get("actuators", status),'
new2 = f'"actuators":   {{k: v for k, v in status.items() if k not in {META_KEYS}}},'
count2 = content.count(old2)
content = content.replace(old2, new2)
print(f'[OK] Fix status endpoint actuators ({count2} occurrences)', flush=True)

# Tulis ke server
import io as _io
sftp = cs.open_sftp()
sftp.putfo(_io.BytesIO(content.encode()), MAIN)
sftp.close()
print('[OK] main.py ditulis ke server', flush=True)

# Upload mqtt_bridge.py (flat publish_status)
sftp = cl.open_sftp()
sftp.put(r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
         f'{PROJ}/hardware/mqtt_bridge.py')
sftp.close()
print('[OK] mqtt_bridge.py uploaded ke lemari-1', flush=True)

# Restart server backend
r(cs, 'docker restart tetasco-backend && sleep 5', 'Restart server')

# Restart lemari-1 backend
r(cl, f'''
PID=$(ss -tlnp | grep ":5001" | grep -oP "pid=\K[0-9]+")
[ -n "$PID" ] && kill -9 $PID && echo "Killed $PID"
sleep 3 && cd {PROJ} && > app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 & echo "PID: $!"
''', 'Restart lemari-1')

print('\n[Tunggu 40 detik untuk MQTT + heartbeat...]\n', flush=True)
time.sleep(40)

r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', 'Sensor endpoint FINAL')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/status | python3 -m json.tool', 'Status endpoint FINAL')

cl.close()
cs.close()
print('\n✅ Done!', flush=True)
