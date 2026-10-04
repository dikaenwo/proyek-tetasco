"""verify_and_fix_status_key.py — Fix sensor_status key + restart server + verify"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

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

# Baca file
i, o, e = cs.exec_command(f'cat {MAIN}')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] main.py: {len(content)} chars, {content.count(chr(10))} lines', flush=True)

# Fix sensor_status key: data.get("sensor_status", "unknown") → data.get("status", data.get("sensor_status", "unknown"))
old_ss = '"sensor_status":data.get("sensor_status", "unknown"),'
new_ss = '"sensor_status":data.get("status", data.get("sensor_status", "unknown")),'
if old_ss in content:
    content = content.replace(old_ss, new_ss, 1)
    print('[OK] Fix sensor_status key (status → sensor_status fallback)', flush=True)
else:
    print(f'[WARN] sensor_status fix target tidak ditemukan', flush=True)

# Tulis kembali
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), MAIN)
sftp.close()
print('[OK] main.py updated', flush=True)

# Restart server untuk pastikan kode terbaru dimuat
r(cs, 'docker restart tetasco-backend && sleep 8', 'Restart server')

# Langsung check setelah restart (sensor + status cache fresh dari lemari-1)
r(cs, 'sleep 5 && curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', 'Sensor endpoint')
r(cs, 'curl -s http://localhost:8000/api/health', 'Health check')

cs.close()
print('\nDone!', flush=True)
