"""fix_lemari1_mqtt.py — Kill duplicate process, restart bersih, test sensor flow"""
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
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Kill SEMUA proses python di lemari-1
r(cl, 'sudo pkill -9 -f python3 2>/dev/null; sleep 2 && ps aux | grep -c python3', '1. Kill all python')

# Restart bersih dengan env vars
r(cl, f'''
cd {PROJ}
> app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 &
echo "Started PID: $!"
''', '2. Start lemari-1 fresh')

time.sleep(10)

# Cek log startup
r(cl, f'tail -20 {PROJ}/app.log', '3. App log (10s setelah start)')

# Monitor MQTT sensor dari server — tunggu 20 detik lebih
print('\n[Tunggu 25 detik untuk sensor publish...]\n', flush=True)
time.sleep(25)

r(cl, f'grep "Sensor\|MQTTBridge.*Connect" {PROJ}/app.log | tail -10', '4. Sensor log lemari-1')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -i "sensor\|mqtt\|lemari" | tail -10', '5. Server sensor logs')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '6. Sensor endpoint')
r(cs, 'curl -s http://localhost:8000/api/sensors', '7. All sensors')

cl.close()
cs.close()
print('\nDone!', flush=True)
