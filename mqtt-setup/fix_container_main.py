"""fix_container_main.py — docker cp main.py ke dalam container + restart"""
import paramiko, sys, io
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

HOST_MAIN = '/home/telur/tetasco-connect/backend/main.py'
CONTAINER_MAIN = '/app/main.py'

# 1. Baca host main.py terbaru
i, o, e = cs.exec_command(f'cat {HOST_MAIN}')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] Host main.py: {len(content)} chars', flush=True)

# Cek dan fix semua:
fixes = 0

# Fix 1: actuators dari sensor endpoint → baca dari status_cache (flat)
old1 = '"actuators":    data.get("actuators",     {}),'
new1 = '"actuators":    {k: v for k, v in device_status_cache.get(device_id, {}).items() if k not in ("ts", "device_id")},'
if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print(f'[OK] Fix 1 sensor endpoint actuators', flush=True)

# Fix 2: sensor_status → "status" key
old2 = '"sensor_status":data.get("sensor_status", "unknown"),'
new2 = '"sensor_status":data.get("status", data.get("sensor_status", "unknown")),'
if old2 in content:
    content = content.replace(old2, new2, 1)
    fixes += 1
    print(f'[OK] Fix 2 sensor_status key', flush=True)

# Fix 3: status endpoint double nesting
old3 = '"actuators":   status,'
new3 = '"actuators":   {k: v for k, v in status.items() if k not in ("ts", "device_id")},'
if old3 in content:
    content = content.replace(old3, new3, 1)
    fixes += 1
    print(f'[OK] Fix 3 status endpoint flat actuators', flush=True)

# Fix sensors list endpoint
old4 = '"actuators":    data.get("actuators",     {}),'
if old4 in content:
    content = content.replace(old4, '{k: v for k, v in device_status_cache.get(device_id, {}).items() if k not in ("ts", "device_id")},')
    fixes += 1
    print(f'[OK] Fix 4 sensors list endpoint', flush=True)

print(f'[INFO] Total fixes: {fixes}', flush=True)

# Tulis ke HOST
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), HOST_MAIN)

# 2. docker cp host → container
r(cs, f'docker cp {HOST_MAIN} tetasco-backend:{CONTAINER_MAIN} && echo "docker cp OK"', '2. docker cp ke container')

# 3. Verify isi container sekarang
r(cs, f'docker exec tetasco-backend grep -n "actuators" {CONTAINER_MAIN} | head -8', '3. Cek container actuators code')

# 4. Restart agar reload kode terbaru  
r(cs, 'docker restart tetasco-backend && sleep 8', '4. Restart container')

# 5. Tunggu heartbeat
print('\n[Tunggu 40 detik untuk heartbeat...]\n', flush=True)
import time; time.sleep(40)

# 6. Final verify
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '5. Sensor endpoint FINAL')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/status | python3 -m json.tool', '6. Status endpoint FINAL')

sftp.close()
cs.close()
print('\n✅ Done!', flush=True)
