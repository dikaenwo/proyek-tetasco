"""fix_and_restart.py — Fix mosquitto.conf dan restart semua container"""
import paramiko, sys, time, io
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
            sys.stdout.write(chunk.decode('utf-8', 'replace'))
            sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# Upload fixed mosquitto.conf
NEW_CONF = """pid_file /run/mosquitto/mosquitto.pid
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

# Listener TCP port 1883
listener 1883
protocol mqtt

# Listener WebSocket port 9001 (untuk Cloudflare Tunnel)
listener 9001
protocol websockets

# Autentikasi
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl.conf

# Tuning
max_keepalive 120
max_inflight_messages 20
max_queued_messages 100
log_type error
log_type warning
log_type notice
log_type information
log_timestamp true
"""

sftp = c.open_sftp()
sftp.putfo(io.BytesIO(NEW_CONF.encode()), f'{PROJ}/mosquitto/config/mosquitto.conf')
sftp.close()
print('[OK] mosquitto.conf fixed & uploaded', flush=True)

# Restart Mosquitto container saja (tidak perlu rebuild)
r(f'docker restart tetasco-mosquitto 2>&1 && sleep 3 && docker ps | grep mosquitto', 'Restart Mosquitto')

# Cek log mosquitto
r(f'docker logs tetasco-mosquitto --tail=15 2>&1', 'Mosquitto logs after fix')

# Start backend & nginx yang depend on mosquitto
r(f'cd {PROJ} && docker compose --env-file .env up -d 2>&1', 'Start remaining services')

time.sleep(8)

r(f'docker ps --format "table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}"', 'All containers status')
r('curl -s http://localhost/api/health 2>/dev/null || echo "API not ready"', 'API health')
r('curl -s http://localhost:8000/ 2>/dev/null || echo "FastAPI not ready"', 'FastAPI direct')

# Test MQTT publish
r('docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 '
  '-u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/test" -m "hello!" 2>&1 && echo "MQTT PUBLISH OK!"', 'MQTT test')

r(f'cd {PROJ} && docker compose logs --tail=20 backend 2>&1', 'Backend logs')

c.close()
print('\nFix & restart complete!', flush=True)
