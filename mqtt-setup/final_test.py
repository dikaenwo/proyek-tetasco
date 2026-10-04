"""final_test.py — Deploy final mqtt_bridge + test sensor flow"""
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

# Upload
sftp = cl.open_sftp()
sftp.put(r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
         f'{PROJ}/hardware/mqtt_bridge.py')
sftp.close()
print('[OK] mqtt_bridge.py uploaded (loop_forever fix)', flush=True)

# Restart
r(cl, f'sudo pkill -9 -f python3 2>/dev/null; sleep 2 && > {PROJ}/app.log && '
      f'cd {PROJ} && set -a && source .env && set +a && '
      f'nohup python3 app.py >> app.log 2>&1 & echo "PID:$!"', '1. Restart lemari-1')

print('[Tunggu 10 detik untuk connect...]\n', flush=True)
time.sleep(10)

r(cl, f'grep "MQTTBridge" {PROJ}/app.log', '2. MQTT logs lemari-1')

print('\n[Tunggu 15 detik untuk sensor publish...]\n', flush=True)
time.sleep(15)

r(cl, f'grep "Sensor\|Connected" {PROJ}/app.log | tail -5', '3. Sensor + Connect log')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -iE "sensor|Sensor|lemari" | tail -5', '4. Server sensor recv')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '5. API sensor endpoint')
r(cs, 'curl -s https://tetasco.my.id/api/tetasco/1/sensor', '6. Via internet (Cloudflare)')

cl.close()
cs.close()
print('\nDone!', flush=True)
