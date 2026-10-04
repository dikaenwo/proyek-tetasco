"""final_deploy_verify.py — Deploy fix actuators + verify final semua data"""
import paramiko, sys, time
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
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Cek server sensor endpoint code (bagian actuators)
r(cs, 'grep -n "actuator\|sensor_cache\|status_cache\|device_id" /home/telur/tetasco-connect/backend/main.py | grep -v "import\|#" | head -20',
  '1. Server endpoint actuators code')

# 2. Upload mqtt_bridge.py dengan fix actuators nesting
sftp = cl.open_sftp()
sftp.put(r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
         f'{PROJ}/hardware/mqtt_bridge.py')
sftp.close()
print('[OK] mqtt_bridge.py uploaded (actuators nested fix)', flush=True)

# 3. Kill + restart
r(cl, f'''
PID=$(ss -tlnp | grep ":5001" | grep -oP "pid=\K[0-9]+")
[ -n "$PID" ] && kill -9 $PID && echo "Killed $PID" || echo "Tidak ada PID"
sleep 3 && cd {PROJ} && > app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 & echo "PID: $!"
''', '2. Restart lemari-1')

print('\n[Tunggu 15 detik untuk MQTT + heartbeat...]\n', flush=True)
time.sleep(15)

r(cl, f'grep "Connected\|MQTTBridge" {PROJ}/app.log | head -5', '3. MQTT log')

print('\n[Tunggu 20 detik untuk heartbeat pertama (t=5s + 30s)...]\n', flush=True)
time.sleep(20)

# 4. Final verify semua endpoint
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '4. Sensor endpoint FINAL')
r(cs, 'curl -s http://localhost:8000/api/devices | python3 -m json.tool', '5. Devices list FINAL')
r(cs, 'curl -s http://localhost:8000/api/health', '6. Health check')

cl.close()
cs.close()
print('\n✅ SELESAI!', flush=True)
