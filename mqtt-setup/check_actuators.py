"""check_actuators.py — Cek actuator data setelah heartbeat"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
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

# Cek MQTT status topic langsung dari Mosquitto
r(cs, '''timeout 5 docker exec tetasco-mosquitto mosquitto_sub \
  -h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" \
  -t "tetasco/lemari-1/status" -C 1 2>&1 | python3 -m json.tool || echo "(no message)"''',
  '1. Status topic langsung dari MQTT')

# Cek sensor endpoint
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '2. Sensor API endpoint')

# Cek log heartbeat di lemari
r(cl, f'grep "heartbeat\|publish_status\|status\|actuator" {PROJ}/app.log | tail -5', '3. Heartbeat log lemari-1')

cs.close()
cl.close()
print('\nDone!', flush=True)
