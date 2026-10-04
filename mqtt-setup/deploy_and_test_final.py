"""deploy_and_test_final.py — Deploy mqtt_bridge fix + test end-to-end sensor"""
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

# Upload mqtt_bridge.py yang sudah difix
sftp = cl.open_sftp()
sftp.put(r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
         f'{PROJ}/hardware/mqtt_bridge.py')
sftp.close()
print('[OK] mqtt_bridge.py uploaded (lazy config fix)', flush=True)

# Restart lemari-1
r(cl, f'sudo pkill -9 -f python3 2>/dev/null; sleep 2; echo killed', '1. Kill processes')
r(cl, f'cd {PROJ} && > app.log && set -a && source .env && set +a && '
      f'nohup python3 app.py >> app.log 2>&1 & echo "PID:$!"', '2. Start backend')

print('[Tunggu 12 detik untuk startup...]\n', flush=True)
time.sleep(12)

r(cl, f'grep "MQTTBridge\|MQTT" {PROJ}/app.log | head -8', '3. MQTT startup log')

print('\n[Tunggu 12 detik lagi untuk sensor publish...]\n', flush=True)
time.sleep(12)

r(cl, f'grep "Sensor\|Connected" {PROJ}/app.log | tail -5', '4. Sensor + Connected log')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -i "sensor\|Sensor"', '5. Server menerima sensor?')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '6. GET sensor endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
