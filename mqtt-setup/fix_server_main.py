"""fix_server_main.py — Fix server main.py: actuators dari status_cache"""
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

MAIN = '/home/telur/tetasco-connect/backend/main.py'

# Baca file
i, o, e = cs.exec_command(f'cat {MAIN}')
content = o.read().decode('utf-8', 'replace')

# Fix 1: get_device_sensor (line 242) — baca actuators dari status_cache
old = '"actuators":    data.get("actuators",     {}),'
new = '"actuators":    device_status_cache.get(device_id, {}).get("actuators", {}),'
if old in content:
    content = content.replace(old, new, 1)
    print('[OK] Fix 1: get_device_sensor actuators', flush=True)
else:
    print(f'[WARN] Fix 1 target tidak ditemukan: {old[:50]}', flush=True)

# Fix 2: get_sensors loop (line 267)
old2 = '"actuators":    data.get("actuators",     {}),'
new2 = '"actuators":    device_status_cache.get(device_id, {}).get("actuators", {}),'
# Ganti semua instance
count = content.count(old2)
content = content.replace(old2, new2)
print(f'[OK] Fix 2: get_sensors actuators ({count} instances)', flush=True)

# Fix 3: status endpoint — hapus double-nesting (line 289: "actuators": status)
# status sekarang = {"actuators": {...}, "ts": ..., "device_id": ...}
# Ubah agar ambil status.get("actuators", status)
old3 = '"actuators":   status,'
new3 = '"actuators":   status.get("actuators", status),'
if old3 in content:
    content = content.replace(old3, new3, 1)
    print('[OK] Fix 3: status endpoint actuators un-nesting', flush=True)
else:
    print(f'[WARN] Fix 3 tidak ditemukan, cek manual', flush=True)

# Tulis kembali
import io as _io
sftp = cs.open_sftp()
sftp.putfo(_io.BytesIO(content.encode()), MAIN)
sftp.close()
print('[OK] main.py ditulis ke server', flush=True)

# Restart backend Docker
r(cs, 'docker restart tetasco-backend && sleep 5 && docker ps | grep backend', 'Restart server backend')

# Verifikasi
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', 'Sensor endpoint FINAL')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/status | python3 -m json.tool', 'Status endpoint FINAL')

cs.close()
print('\nDone!', flush=True)
