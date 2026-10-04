"""check_and_fix.py — Cek sensor cache + fix postgres"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ_L = '/home/tetasco1/Penetas-Telur/backend'
PROJ_S = '/home/telur/tetasco-connect'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(60)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# ── 1. Fix postgres (tetap restarting) ───────────────────────────────────────
r(cs, 'docker logs tetasco-postgres --tail=5 2>&1', '1. Postgres logs')
# Restart postgres fresh
r(cs, 'docker stop tetasco-postgres 2>/dev/null; '
      'docker rm tetasco-postgres 2>/dev/null; '
      f'cd {PROJ_S} && docker compose --env-file .env up -d database 2>&1 | tail -5',
  '2. Restart postgres fresh')
time.sleep(8)
r(cs, 'docker ps --format "{{.Names}}\t{{.Status}}"', '3. Container status')

# ── 2. Pastikan lemari-1 running dan MQTT terhubung ──────────────────────────
r(cl, f'ps aux | grep -c "python.*app.py" | grep -v grep', '4. Lemari-1 process check')
r(cl, f'grep "MQTTBridge.*Connected\|Sensor publish" {PROJ_L}/app.log | tail -5', '5. MQTT + sensor log lemari-1')

# ── 3. Tunggu lemari-1 publish sensor lalu test endpoint ─────────────────────
print('\n[Menunggu 20 detik untuk sensor data...]\n', flush=True)
time.sleep(20)

r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '6. Sensor lemari-1')
r(cs, 'curl -s http://localhost:8000/api/sensors | python3 -m json.tool',          '7. Semua sensor')
r(cs, 'curl -s http://localhost/api/tetasco/1/sensor | python3 -m json.tool',      '8. Via Nginx (public endpoint)')

# ── 4. Live test: monitor MQTT messages di server ────────────────────────────
r(cs, 'docker logs tetasco-backend --tail=10 2>&1', '9. Backend MQTT logs terbaru')

cs.close()
cl.close()
print('\nDone!', flush=True)
