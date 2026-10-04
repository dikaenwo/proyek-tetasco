"""debug_cache.py — Cek isi semua cache server + key format"""
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

# 1. Lihat seluruh cache via all/status endpoint
r(cs, 'curl -s http://localhost:8000/api/tetasco/all/status | python3 -m json.tool', '1. All status (semua cache)')

# 2. Cek bagaimana mqtt_manager extract device_id dari topic
r(cs, 'grep -n "on_status\|on_message\|device_id\|topic" /home/telur/tetasco-connect/backend/mqtt_manager.py | head -20',
  '2. MQTT manager topic parsing')

# 3. Cek device_id_from_tetasco_id function
r(cs, 'grep -n "def device_id_from\|return.*lemari\|return f" /home/telur/tetasco-connect/backend/main.py | head -10',
  '3. device_id_from_tetasco_id function')

cs.close()
print('\nDone!', flush=True)
