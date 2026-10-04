"""try_ws_local.py — Test WebSocket port 9001 lokal (sama seperti versi pertama berhasil)"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

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

# 1. Test dulu: apakah WebSocket port 9001 bisa diakses dari lemari-1?
r(cl, 'nc -z -w 3 192.168.1.14 9001 && echo "WS 9001 OK" || echo "WS 9001 FAIL"', '1. Test port 9001 dari lemari-1')

# 2. Test paho WebSocket lokal (tanpa TLS)
r(cl, '''timeout 15 python3 << 'PYEOF' 2>&1
import paho.mqtt.client as m, time

connected = False
def on_connect(c, ud, flags, rc, props=None):
    global connected
    connected = rc == 0
    print(f"WS on_connect rc={rc}, ok={connected}", flush=True)
def on_log(c, ud, level, buf):
    if level <= 16: print(f"LOG: {buf}", flush=True)

c = m.Client(client_id="test-ws-local", transport="websockets",
             protocol=m.MQTTv5, callback_api_version=m.CallbackAPIVersion.VERSION2)
c.ws_set_options(path="/mqtt")
c.username_pw_set("lemari-1", "lem1-IJjLZ7QCc2RI8UyC")
c.on_connect = on_connect
c.on_log = on_log
c.connect_async("192.168.1.14", 9001, 30)
c.loop_start()
time.sleep(8)
c.loop_stop()
print(f"WS local 9001: {'CONNECTED!' if connected else 'FAILED'}", flush=True)
PYEOF
''', '2. Test WebSocket lokal (no TLS)')

# 3. Update .env ke WebSocket lokal
NEW_ENV = (
    'DEVICE_ID=lemari-1\n'
    'MQTT_BROKER=192.168.1.14\n'
    'MQTT_PORT=9001\n'
    'MQTT_TRANSPORT=websockets\n'
    'MQTT_USE_TLS=false\n'
    'MQTT_WEBSOCKET_PATH=/mqtt\n'
    'MQTT_USER=lemari-1\n'
    'MQTT_PASS=lem1-IJjLZ7QCc2RI8UyC\n'
    'SENSOR_INTERVAL=10\n'
    'HEARTBEAT_INTERVAL=30\n'
)
sftp = cl.open_sftp()
sftp.putfo(io.BytesIO(NEW_ENV.encode()), f'{PROJ}/.env')
sftp.close()
print('[OK] .env → WebSocket 192.168.1.14:9001 (no TLS)', flush=True)

# Kill port 5001 dan restart
r(cl, f'''
sudo fuser -k 5001/tcp 2>/dev/null
sleep 3
nc -z 127.0.0.1 5001 && echo "PORT MASIH BUSY" || echo "PORT BEBAS"
''', '3. Kill + cek port')

r(cl, f'''
cd {PROJ} && > app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
''', '4. Start backend')

print('\n[Tunggu 15 detik untuk MQTT + sensor...]\n', flush=True)
time.sleep(15)

r(cl, f'grep "MQTTBridge\|Serving\|Address" {PROJ}/app.log | head -15', '5. MQTT + Flask log')

time.sleep(10)
r(cl, f'grep "Connected\|Sensor publish" {PROJ}/app.log | tail -5', '6. Connected + sensor log')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -iE "sensor|lemari" | tail -5', '7. Server recv sensor')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '8. API endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
