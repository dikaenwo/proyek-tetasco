"""launch.py — Start semua container Tetasco"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, get_pty=True)
    o.channel.settimeout(300)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace'))
            sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# Cek apakah backend image sudah ada (dari build sebelumnya)
r('docker images | grep -E "NAME|tetasco|mosquitto|nginx|postgres"', 'Available images')

# Stop semua container lama yang mungkin konflik
r('docker stop tetasco-backend tetasco-postgres tetasco-nginx tetasco-mosquitto 2>/dev/null || true', 'Stop old containers')
r('docker rm tetasco-backend tetasco-postgres tetasco-nginx tetasco-mosquitto 2>/dev/null || true', 'Remove old containers')

# Jalankan docker compose dari folder yang benar
print(f'\n[docker compose up dari {PROJ}]', flush=True)
r(f'cd {PROJ} && docker compose --env-file .env up -d --build 2>&1', 'Docker Compose UP')

# Tunggu services ready
print('\n[Waiting 10s...]', flush=True)
time.sleep(10)

r(f'cd {PROJ} && docker compose ps', 'Container status')
r('curl -s http://localhost/api/health', 'API health check')
r('curl -s http://localhost:8000/', 'FastAPI direct check')

# Test MQTT
r('docker exec tetasco-mosquitto mosquitto_pub -h localhost -p 1883 '
  '-u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/test" -m "hello_mqtt" 2>&1 && echo "MQTT OK!"', 'MQTT test')

r(f'cd {PROJ} && docker compose logs --tail=20 backend 2>&1', 'Backend logs')
r(f'cd {PROJ} && docker compose logs --tail=10 mosquitto 2>&1', 'Mosquitto logs')

c.close()
print('\nLaunch complete!', flush=True)
