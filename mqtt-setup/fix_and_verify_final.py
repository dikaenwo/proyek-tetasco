"""fix_and_verify_final.py — Cek server code actuators + status dari MQTT + final verify"""
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

# 1. Cek bagaimana server handle status topic → actuators
r(cs, 'grep -n "status\|actuator\|device_status" /home/telur/tetasco-connect/backend/main.py | head -20',
  '1. Server: status/actuator handler')

# 2. Cek apa yang gpio_controller.get_all_actuators() kembalikan di lemari-1
r(cl, '''timeout 5 python3 << 'PYEOF' 2>&1
import sys
sys.path.insert(0, "/home/tetasco1/Penetas-Telur/backend")
from hardware.gpio_controller import gpio_controller as gpio
result = gpio.get_all_actuators()
print("Actuators:", result)
print("Type:", type(result))
PYEOF
''', '2. gpio_controller.get_all_actuators() output')

# 3. Subscribe ke status topic lebih lama (40 detik untuk tangkap heartbeat)
print('\n[Subscribe MQTT 40 detik untuk tangkap heartbeat...]\n', flush=True)
r(cs, '''timeout 40 docker exec tetasco-mosquitto mosquitto_sub \
  -h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" \
  -t "tetasco/lemari-1/status" -t "tetasco/lemari-1/heartbeat" \
  -v -C 2 2>&1 | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            try:
                data = json.loads(parts[1])
                print(f\\"Topic: {parts[0]}\\")
                for k,v in data.items():
                    print(f\\"  {k}: {v}\\")
                print()
            except:
                print(line)
" || echo "(timeout, tidak ada pesan)"''', '3. Subscribe status+heartbeat (40s)')

# 4. Final sensor API
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '4. Final sensor API')

cl.close()
cs.close()
print('\nDone!', flush=True)
