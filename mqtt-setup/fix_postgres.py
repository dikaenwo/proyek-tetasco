import paramiko, sys, time
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

# Cek log postgres
r('docker logs tetasco-postgres --tail 20 2>&1', '1. Postgres log')
r('docker inspect tetasco-postgres --format "{{.State.ExitCode}} {{.State.Error}}" 2>&1', '2. Postgres exit code')

# Fix: kadang postgres corrupt karena unclean shutdown
# Coba force start postgres standalone dulu
r('docker compose -f ~/tetasco-connect/docker-compose.yml stop database 2>/dev/null; sleep 2; docker compose -f ~/tetasco-connect/docker-compose.yml start database 2>&1', '3. Restart postgres only', timeout=15)
time.sleep(8)
r('docker logs tetasco-postgres --tail 10 2>&1', '4. Postgres log setelah restart')
r('docker exec tetasco-postgres pg_isready -U telur -d tetasco 2>&1', '5. pg_isready check')

# Start backend
r('cd ~/tetasco-connect && docker compose up -d backend 2>&1 | tail -5', '6. Start backend', timeout=30)
time.sleep(10)
r('curl -s http://localhost:8000/api/health 2>/dev/null || echo "not ready"', '7. Backend health')
r('curl -s "http://localhost:8000/api/tetasco/1/camera/stats" 2>/dev/null', '8. Camera stats')
r('docker ps --format "{{.Names}}\\t{{.Status}}" 2>/dev/null', '9. Container status')

sv.close()
