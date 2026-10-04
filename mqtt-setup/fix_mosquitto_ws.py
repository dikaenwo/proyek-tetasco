"""fix_mosquitto_ws.py — Fix Mosquitto WebSocket port 9001"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Cek Mosquitto listening ports
r('docker exec tetasco-mosquitto netstat -tlnp 2>/dev/null || '
  'docker exec tetasco-mosquitto ss -tlnp', '1. Mosquitto listening ports')

# 2. Cek dari nginx apakah bisa reach mosquitto:9001
r('docker exec tetasco-nginx sh -c "wget -q --timeout=3 http://mosquitto:9001/ -O- 2>&1 | head -5 || echo FAIL"',
  '2. Nginx → mosquitto:9001 test')

# 3. Cek isi mosquitto.conf di container
r('docker exec tetasco-mosquitto cat /mosquitto/config/mosquitto.conf', '3. Mosquitto config')

# 4. Cek apakah port 9001 exposed keluar
r('docker port tetasco-mosquitto', '4. Mosquitto exposed ports')

# 5. Test dari dalam server langsung ke port 9001
r('nc -z -w 2 127.0.0.1 9001 && echo "9001 OK" || echo "9001 NOT LISTENING"',
  '5. Port 9001 dari host')

# 6. Cek Mosquitto logs untuk 9001
r('docker logs tetasco-mosquitto --tail=15 2>&1 | grep -E "9001|websocket|listen|port"',
  '6. Mosquitto log filter 9001')

c.close()
print('\nDone!', flush=True)
