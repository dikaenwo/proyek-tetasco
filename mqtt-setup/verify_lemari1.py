"""verify_lemari1.py — Verifikasi lemari-1 running stable + sensor data live"""
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
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

r(cl, 'ss -tlnp | grep 5001', '1. Flask port status')
r(cl, f'grep "Connected\|Sensor\|heartbeat\|Error" {PROJ}/app.log | tail -10', '2. MQTT bridge logs')
r(cs, 'docker logs tetasco-backend --since=2m 2>&1 | grep -iE "sensor|lemari|heart" | tail -10', '3. Server recv')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '4. Sensor endpoint')
r(cs, 'curl -s http://localhost:8000/api/devices | python3 -m json.tool', '5. Devices endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
