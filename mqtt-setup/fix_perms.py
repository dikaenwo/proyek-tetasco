"""fix_perms.py — Fix file permissions dan restart Mosquitto"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, get_pty=True)
    o.channel.settimeout(60)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# Fix permissions - mosquitto container runs as uid 1883
# passwd & acl.conf harus readable oleh mosquitto user
r(f'ls -la {PROJ}/mosquitto/config/', 'Cek permissions sekarang')
r(f'chmod 644 {PROJ}/mosquitto/config/passwd {PROJ}/mosquitto/config/acl.conf {PROJ}/mosquitto/config/mosquitto.conf && '
  f'ls -la {PROJ}/mosquitto/config/', 'Fix chmod 644')

# Restart mosquitto
r('docker restart tetasco-mosquitto && sleep 5 && docker logs tetasco-mosquitto --tail=15 2>&1', 'Restart Mosquitto')
r('docker ps | grep mosquitto', 'Mosquitto status')

# Test MQTT
r('sleep 3 && docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 '
  '-u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/test" -m "halo!" 2>&1 && echo "=== MQTT PUBLISH OK! ==="', 'MQTT test')

# Setelah mosquitto healthy, compose up sisa containers
time.sleep(5)
r(f'cd {PROJ} && docker compose --env-file .env up -d 2>&1 | tail -20', 'Start backend & nginx')
time.sleep(10)

r('docker ps', 'Final container status')
r('curl -s http://localhost/api/health', 'API health')
r('docker logs tetasco-backend --tail=20 2>&1', 'Backend logs')

c.close()
print('\nDone!', flush=True)
