"""fix_server_actuators.py — Cek + fix server endpoint untuk baca actuators dari status_cache"""
import paramiko, sys
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

# 1. Cek sensor endpoint code lengkap di server
r(cs, 'grep -n "tetasco_id/sensor\|sensor_cache\|status_cache\|actuator\|def get_device" /home/telur/tetasco-connect/backend/main.py',
  '1. Sensor endpoint code server')

# 2. Lihat fungsi sensor endpoint full
r(cs, 'awk "/api\/tetasco\/{tetasco_id}\/sensor/,/^@app/" /home/telur/tetasco-connect/backend/main.py | head -40',
  '2. Sensor endpoint function')

# 3. Cek isi device_status_cache sekarang (via FastAPI debug)
r(cs, '''curl -s http://localhost:8000/api/tetasco/1/status 2>/dev/null | python3 -m json.tool || \
curl -s http://localhost:8000/api/tetasco/1/actuators 2>/dev/null | python3 -m json.tool || echo "endpoint tidak ada"''',
  '3. Status/actuator endpoint')

# 4. Lihat semua endpoint di server
r(cs, 'grep -n "^@app\." /home/telur/tetasco-connect/backend/main.py | head -20',
  '4. Semua API endpoints di server')

cs.close()
print('\nDone!', flush=True)
