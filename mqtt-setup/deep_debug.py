"""deep_debug.py — Cek systemd service + full app.log + MQTT verbose"""
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

# 1. Cek systemd services untuk tetasco/penetas
r(cl, '''
echo "=== Systemd services tetasco ==="
sudo systemctl list-units --type=service | grep -iE "tetasco|penetas|flask|python"
echo "=== /etc/systemd/system/ ==="
ls /etc/systemd/system/ | grep -iE "tetasco|penetas|flask|python" 2>/dev/null || echo "(tidak ada)"
echo "=== /lib/systemd/system/ ==="
ls /lib/systemd/system/ | grep -iE "tetasco|penetas" 2>/dev/null || echo "(tidak ada)"
echo "=== ~/.config/systemd/ ==="
ls ~/.config/systemd/user/ 2>/dev/null || echo "(tidak ada)"
''', '1. Systemd services')

# 2. Siapa yang memegang port 5001?
r(cl, '''
echo "=== Port 5001 holder ==="
sudo ss -tlnp | grep 5001
echo "=== ps aux untuk PID di port 5001 ==="
PID=$(sudo ss -tlnp | grep ":5001" | grep -oP "pid=\K[0-9]+")
echo "PID: $PID"
sudo ps aux | grep $PID | grep -v grep
echo "=== Semua python processes ==="
sudo ps aux | grep python | grep -v grep
''', '2. Port 5001 holder detail')

# 3. Full app.log (tidak difilter)
r(cl, f'wc -l {PROJ}/app.log && tail -30 {PROJ}/app.log', '3. Full app.log tail')

# 4. Test: apa yang terjadi jika langsung import mqtt_bridge setelah Flask start?
r(cl, '''timeout 20 python3 << 'PYEOF' 2>&1
import os, sys, time, logging, threading
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(name)s: %(message)s")

os.environ.update({
    "DEVICE_ID": "lemari-1",
    "MQTT_BROKER": "192.168.1.14",
    "MQTT_PORT": "9001",
    "MQTT_TRANSPORT": "websockets",
    "MQTT_USE_TLS": "false",
    "MQTT_WEBSOCKET_PATH": "/mqtt",
    "MQTT_USER": "lemari-1",
    "MQTT_PASS": "lem1-IJjLZ7QCc2RI8UyC",
})

sys.path.insert(0, "/home/tetasco1/Penetas-Telur/backend")

# Simulasi Flask thread
import flask
app2 = flask.Flask("test_app")
def fake_flask():
    # Jangan bind port, hanya simulasi context
    pass

from hardware.mqtt_bridge import mqtt_bridge as bridge
bridge._started = False  # reset flag
print("Calling start()...", flush=True)
bridge.start(gpio_controller=None, sensor_manager=None)
print(f"start() done, connected={bridge.connected}", flush=True)

for i in range(15):
    time.sleep(1)
    print(f"t={i+1}s connected={bridge.connected}", flush=True)
    if bridge.connected:
        print("CONNECTED!", flush=True)
        break
PYEOF
''', '4. Test MQTT standalone (tanpa Flask bind)')

cl.close()
cs.close()
print('\nDone!', flush=True)
