import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RASPI_IP   = '192.168.1.27'
RASPI_USER = 'tetasco1'
RASPI_PASS = 'saumata1192'
SERVER_IP  = '192.168.1.14'
MQTT_BROKER   = SERVER_IP
MQTT_PORT     = 1883
MQTT_USER     = 'lemari-1'
MQTT_PASSWORD = 'lemari1-mqtt-2026'
DEVICE_ID     = 'lemari-1'

# File MQTT subscriber — tulis langsung ke disk, hindari format() clash
MQTT_SUB_FILE = r"""# mqtt_subscriber.py — MQTT instant control untuk Raspi Lemari
# Dipanggil dari app.py: from hardware.mqtt_subscriber import start_mqtt_subscriber
import threading, json, time, logging
logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    _PAHO_OK = True
except ImportError:
    _PAHO_OK = False
    logger.warning("[MQTT-Sub] pip3 install paho-mqtt")

BROKER   = "192.168.1.14"
PORT     = 1883
USERNAME = "lemari-1"
PASSWORD = "lemari1-mqtt-2026"
TOPIC    = "tetasco/lemari-1/command/#"
_gpio    = None

def _on_message(client, userdata, msg):
    global _gpio
    try:
        data     = json.loads(msg.payload.decode())
        actuator = msg.topic.split("/")[-1]
        state    = bool(data.get("state", False))
        if _gpio is None:
            return
        if actuator == "emergency_stop":
            for dev in ["fan", "lamp_1", "lamp_2", "mist_maker", "motor"]:
                _gpio.set_actuator(dev, False)
            logger.info("[MQTT-Cmd] Emergency Stop!")
        else:
            _gpio.set_actuator(actuator, state)
            logger.info(f"[MQTT-Cmd] INSTANT: {actuator}={'ON' if state else 'OFF'}")
    except Exception as e:
        logger.error(f"[MQTT-Cmd] Error: {e}")

def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC, qos=1)
        logger.info(f"[MQTT-Sub] Connected & subscribed: {TOPIC}")
    else:
        logger.warning(f"[MQTT-Sub] Connect failed rc={rc}")

def _on_disconnect(client, userdata, rc):
    logger.warning(f"[MQTT-Sub] Disconnected rc={rc}, reconnecting...")

def start_mqtt_subscriber(gpio_controller):
    global _gpio
    if not _PAHO_OK:
        logger.error("[MQTT-Sub] paho-mqtt not installed!")
        return
    _gpio = gpio_controller
    def _run():
        while True:
            try:
                c = mqtt.Client(client_id="lemari-1-sub", clean_session=True)
                c.username_pw_set(USERNAME, PASSWORD)
                c.on_connect    = _on_connect
                c.on_message    = _on_message
                c.on_disconnect = _on_disconnect
                c.reconnect_delay_set(min_delay=2, max_delay=30)
                c.connect(BROKER, PORT, keepalive=60)
                c.loop_forever()
            except Exception as e:
                logger.warning(f"[MQTT-Sub] Error: {e}, retry 5s...")
                time.sleep(5)
    threading.Thread(target=_run, daemon=True, name="mqtt-sub").start()
    logger.info("[MQTT-Sub] Subscriber started in background")
"""

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect(RASPI_IP, 22, RASPI_USER, RASPI_PASS, timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect(SERVER_IP, 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=30):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')
    return out

def ras_bg(cmd):
    transport = rp.get_transport()
    chan = transport.open_session()
    chan.exec_command(cmd)
    time.sleep(0.5)
    chan.close()

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# 1. Install paho-mqtt
print('=== 1. Install paho-mqtt ===')
ras('pip3 install paho-mqtt --quiet 2>&1 | tail -2', 'pip install')
ras("python3 -c 'import paho.mqtt.client; print(\"paho-mqtt OK\")'", 'verify')

# 2. Upload mqtt_subscriber.py
print('\n=== 2. Upload mqtt_subscriber.py ===')
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(MQTT_SUB_FILE.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/mqtt_subscriber.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/mqtt_subscriber.py && echo OK', 'Syntax check')

# 3. Tambahkan import ke app.py
print('\n=== 3. Patch app.py ===')
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')

if 'mqtt_subscriber' in app_py:
    print('[INFO] Sudah ada import mqtt_subscriber')
else:
    OLD = 'cloud_sync.start(sensor_manager, gpio_controller)'
    NEW = ('cloud_sync.start(sensor_manager, gpio_controller)\n\n'
           '    # ── MQTT Subscriber: instant GPIO via MQTT (< 50ms) ──\n'
           '    from hardware.mqtt_subscriber import start_mqtt_subscriber\n'
           '    start_mqtt_subscriber(gpio_controller)')
    if OLD in app_py:
        app_py = app_py.replace(OLD, NEW, 1)
        sftp2 = rp.open_sftp()
        sftp2.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
        sftp2.close()
        print('[OK] app.py diupdate dengan start_mqtt_subscriber')
    else:
        print('[WARN] Pattern tidak ditemukan di app.py')
        print(app_py[app_py.find('cloud_sync'):app_py.find('cloud_sync')+100])

# 4. Restart Raspi
print('\n=== 4. Restart Raspi app ===')
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo ok', 'Kill old')
ras_bg('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
print('[OK] App started')
time.sleep(12)
ras('pgrep -fa "python3 backend/app.py" | grep -v pgrep | head -1', 'Process')
ras('tail -20 /tmp/tetasco_backend.log', 'Log (cari MQTT-Sub)')

# 5. Test timing
print('\n=== 5. Test instant control ===')
time.sleep(5)
for action in ['on', 'off', 'on']:
    t0 = time.time()
    i2,o2,_ = sv.exec_command(f"curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/{action}")
    r = o2.read().decode('utf-8','replace').strip()
    elapsed = (time.time()-t0)*1000
    print(f'  Fan {action}: {elapsed:.0f}ms — {r[:50]}')
    time.sleep(0.5)

srv('docker logs tetasco-backend --tail 5 2>&1 | grep -i "mqtt\\|direct\\|instant"', 'Server log')

rp.close()
sv.close()
print('\n✅ Done! MQTT instant control deployed!')
