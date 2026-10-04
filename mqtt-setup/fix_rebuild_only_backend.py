"""fix_rebuild_only_backend.py — Build backend only, restart tanpa recreate postgres/mosquitto"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, get_pty=True)
    o.channel.settimeout(120)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# 1. Pastikan mosquitto dan postgres masih up (cek status)
r('docker ps --format "{{.Names}}\t{{.Status}}"', '1. Container status sekarang')

# 2. Jika ada yang down, start ulang tanpa build
r(f'cd {PROJ} && docker compose --env-file .env up -d mosquitto database 2>&1 | tail -10', '2. Start mosquitto & postgres')
time.sleep(10)

# 3. Build HANYA backend, lalu restart dengan --no-deps (tidak sentuh dependencies)
r(f'cd {PROJ} && docker compose build backend 2>&1 | tail -5', '3. Build backend only')
r(f'cd {PROJ} && docker compose --env-file .env up -d --no-deps backend nginx 2>&1 | tail -10', '4. Start backend (no-deps)')
time.sleep(8)

r('docker ps --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"', '5. Container status akhir')
r('docker logs tetasco-backend --tail=12 2>&1', '6. Backend logs')

# Test sensor endpoints
time.sleep(3)
r('curl -s http://localhost:8000/api/tetasco/1/sensor', '7. GET /api/tetasco/1/sensor')
r('curl -s http://localhost:8000/api/sensors', '8. GET /api/sensors')
r('curl -s http://localhost:8000/api/devices', '9. GET /api/devices')

c.close()
print('\nDone!', flush=True)
