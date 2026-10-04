"""fix_lemari1_local.py — Switch lemari-1 ke koneksi TCP lokal (port 1883 langsung)"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Update .env lemari-1: gunakan TCP lokal (server di LAN yang sama)
NEW_ENV = (
    'DEVICE_ID=lemari-1\n'
    'MQTT_BROKER=192.168.1.14\n'   # IP server di LAN
    'MQTT_PORT=1883\n'              # TCP langsung, no WebSocket
    'MQTT_TRANSPORT=tcp\n'
    'MQTT_USE_TLS=false\n'
    'MQTT_WEBSOCKET_PATH=/mqtt\n'   # tidak dipakai, tapi disimpan
    'MQTT_USER=lemari-1\n'
    'MQTT_PASS=lem1-IJjLZ7QCc2RI8UyC\n'
    'SENSOR_INTERVAL=10\n'
    'HEARTBEAT_INTERVAL=30\n'
)

sftp = cl.open_sftp()
sftp.putfo(io.BytesIO(NEW_ENV.encode()), f'{PROJ}/.env')
sftp.close()
print('[OK] .env updated → TCP lokal 192.168.1.14:1883', flush=True)

# Restart lemari-1
r(cl, f'sudo pkill -9 -f python3 2>/dev/null; sleep 2; echo killed', '1. Kill processes')
r(cl, f'cd {PROJ} && > app.log && set -a && source .env && set +a && '
      f'nohup python3 app.py >> app.log 2>&1 & echo "PID:$!"', '2. Start lemari-1')

time.sleep(12)
r(cl, f'grep "MQTTBridge\|Sensor" {PROJ}/app.log | head -15', '3. MQTT log lemari-1')

print('\n[Tunggu 15 detik untuk sensor publish...]\n', flush=True)
time.sleep(15)

r(cl, f'grep "Sensor publish\|Connected" {PROJ}/app.log | tail -5', '4. Sensor publish log')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -i "sensor\|Sensor\|lemari"', '5. Server sensor log')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '6. Sensor endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
