"""hot_deploy.py — Upload mqtt_bridge.py + restart lemari-1 + verify sensor_type & actuators"""
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
    o.channel.settimeout(25)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Upload
sftp = cl.open_sftp()
sftp.put(r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
         f'{PROJ}/hardware/mqtt_bridge.py')
sftp.close()
print('[OK] mqtt_bridge.py uploaded (sensor_type + actuators fix)', flush=True)

# Kill + restart
r(cl, f'''
PID=$(ss -tlnp | grep ":5001" | grep -oP "pid=\K[0-9]+")
echo "Killing PID: $PID"
kill -9 $PID 2>/dev/null
sleep 3
ss -tlnp | grep 5001 || echo "Port BEBAS"
''', '1. Kill proses')

r(cl, f'''
cd {PROJ} && > app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
''', '2. Start backend')

print('\n[Tunggu 20 detik...]\n', flush=True)
time.sleep(20)

r(cl, f'grep "MQTTBridge\|Connected" {PROJ}/app.log | head -5', '3. MQTT log')

print('\n[Tunggu 15 detik untuk heartbeat + sensor...]\n', flush=True)
time.sleep(15)

r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '4. Sensor endpoint (lengkap)')

cl.close()
cs.close()
print('\nDone!', flush=True)
