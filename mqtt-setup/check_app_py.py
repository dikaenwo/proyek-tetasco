"""check_app_py.py — Lihat app.py dan test mqtt_bridge.start() langsung"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
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

# Lihat bagian mqtt_bridge di app.py
r(cl, f'grep -n "mqtt_bridge\|MQTT\|sensor_manager\|gpio_controller" {PROJ}/app.py | tail -30',
  '1. Bagian MQTT di app.py')

# Lihat full app.log dari run terakhir (semua log)
r(cl, f'cat {PROJ}/app.log | head -30', '2. app.log awal (full, tidak difilter)')

# Test: jalankan mqtt_bridge.start() langsung TANPA Flask (standalone test)
r(cl, f'''timeout 25 python3 << 'PYEOF' 2>&1
import os, sys, time, logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s: %(message)s')

os.environ.update({{
    "DEVICE_ID": "lemari-1",
    "MQTT_BROKER": "192.168.1.14",
    "MQTT_PORT": "1883",
    "MQTT_TRANSPORT": "tcp",
    "MQTT_USE_TLS": "false",
    "MQTT_USER": "lemari-1",
    "MQTT_PASS": "lem1-IJjLZ7QCc2RI8UyC",
    "SENSOR_INTERVAL": "5",
    "HEARTBEAT_INTERVAL": "10",
}})

sys.path.insert(0, "{PROJ}")
from hardware.mqtt_bridge import mqtt_bridge

print("Calling mqtt_bridge.start()...", flush=True)
mqtt_bridge.start(gpio_controller=None, sensor_manager=None)
print(f"start() returned! connected={{mqtt_bridge.connected}}", flush=True)

for i in range(20):
    time.sleep(1)
    print(f"t={{i+1}}s connected={{mqtt_bridge.connected}}", flush=True)
    if mqtt_bridge.connected:
        print("CONNECTED!", flush=True)
        break
PYEOF
''', '3. Standalone test mqtt_bridge.start()')

cl.close()
print('\nDone!', flush=True)
