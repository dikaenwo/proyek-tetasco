"""reboot_and_start.py — Reboot lemari-1, tunggu online, start backend, verifikasi"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def ssh_connect(host, user, password, retries=10, delay=8):
    for i in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(host, 22, user, password, timeout=8)
            return c
        except Exception as e:
            print(f'  SSH attempt {i+1}/{retries}: {e}', flush=True)
            time.sleep(delay)
    return None

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def rs(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Reboot lemari-1
print('\n[Reboot lemari-1...]\n', flush=True)
cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
try:
    cl.exec_command('sudo reboot')
except: pass
cl.close()
print('Reboot command sent. Menunggu 40 detik...', flush=True)
time.sleep(40)

# 2. Tunggu lemari-1 online kembali
print('\n[Menunggu lemari-1 online...]\n', flush=True)
cl = ssh_connect('192.168.1.27', 'tetasco1', 'saumata1192', retries=15, delay=8)
if not cl:
    print('ERROR: lemari-1 tidak bisa dihubungi setelah reboot!', flush=True)
    sys.exit(1)
print('Lemari-1 online!', flush=True)

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

# 3. Cek port 5001 bersih
r(cl, 'ss -tlnp | grep 5001 || echo "PORT 5001 BERSIH!"', '1. Port 5001 setelah reboot')

# 4. Start backend
r(cl, f'''
cd {PROJ}
> app.log
set -a && source .env && set +a
echo "Config: transport=$MQTT_TRANSPORT broker=$MQTT_BROKER:$MQTT_PORT"
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
''', '2. Start backend')

print('\n[Tunggu 15 detik untuk startup + MQTT connect...]\n', flush=True)
time.sleep(15)

r(cl, f'cat {PROJ}/app.log | grep -v werkzeug | head -20', '3. App.log startup')
time.sleep(12)

r(cl, f'grep "Connected\|Sensor\|MQTTBridge\|Connecting" {PROJ}/app.log | tail -8', '4. MQTT status')
rs(cs, 'docker logs tetasco-backend --since=40s 2>&1 | grep -iE "sensor|lemari" | tail -5', '5. Server sensor recv')
rs(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '6. Sensor endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
