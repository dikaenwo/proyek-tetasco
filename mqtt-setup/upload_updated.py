"""upload_updated.py — Upload file relay terbaru ke server"""
import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

sftp = c.open_sftp()
files = [
    (r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\relay_api_mqtt.py', f'{PROJ}/relay_api_mqtt.py'),
    (r'd:\Proyek Penetas Telur\mqtt-setup\mosquitto\config\mosquitto.conf', f'{PROJ}/mosquitto/config/mosquitto.conf'),
    (r'd:\Proyek Penetas Telur\mqtt-setup\docker-compose.yml', f'{PROJ}/docker-compose.yml'),
]
for local, remote in files:
    sftp.put(local, remote)
    print(f'[UP] {os.path.basename(local)}', flush=True)

sftp.close()

# Test MQTT via path /mqtt (dari dalam server, simulasi WebSocket client)
def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    print(out if out else '(empty)', flush=True)
    return out

r('curl -s http://localhost/api/health', 'API health')
r('docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/test" -m "via_nginx_path" && echo "MQTT TCP OK"', 'MQTT TCP test')
r('docker logs tetasco-nginx --tail=5 2>&1', 'Nginx logs')

c.close()
print('\nDone! File terbaru sudah di upload.', flush=True)
