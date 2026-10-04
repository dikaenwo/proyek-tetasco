import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# Baca docker-compose.yml dan ganti postgres:15-alpine → postgres:16-alpine
i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
dc = o.read().decode('utf-8','replace')

if 'postgres:15' in dc:
    dc = dc.replace('postgres:15-alpine', 'postgres:16-alpine', 1)
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(dc.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
    sftp.close()
    print('[OK] docker-compose.yml: postgres 15 → 16')
elif 'postgres:16' in dc:
    print('[INFO] Sudah postgres:16')

# Pull image baru dan restart
r('docker pull postgres:16-alpine 2>&1 | tail -3', '1. Pull postgres:16', timeout=120)
r('cd ~/tetasco-connect && docker compose up -d database 2>&1 | tail -5', '2. Start database', timeout=30)
time.sleep(12)
r('docker logs tetasco-postgres --tail 8 2>&1', '3. Postgres log')
r('docker exec tetasco-postgres pg_isready -U telur -d tetasco 2>&1', '4. pg_isready')

# Start backend
r('cd ~/tetasco-connect && docker compose up -d backend nginx 2>&1 | tail -5', '5. Start backend + nginx', timeout=30)
time.sleep(10)
r('curl -s http://localhost:8000/api/health 2>/dev/null | head -1', '6. Backend health')
r('curl -s "http://localhost:8000/api/tetasco/1/camera/stats" 2>/dev/null', '7. Camera stats')
r('docker ps --format "{{.Names}}\\t{{.Status}}"', '8. Container status')

sv.close()
print('\n✅ Done!')
