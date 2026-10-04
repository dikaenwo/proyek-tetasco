"""debug_live.py — Debug MQTT langsung di lemari-1"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(40)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Test standalone mqtt_bridge dengan paho logging diaktifkan
r(cl, '''timeout 20 python3 << 'PYEOF' 2>&1
import logging, os, sys, time
# Aktifkan semua paho log
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s', stream=sys.stdout)

# Set env vars dulu seperti .env
os.environ.update({
    "DEVICE_ID": "lemari-1",
    "MQTT_BROKER": "192.168.1.14",
    "MQTT_PORT": "1883",
    "MQTT_TRANSPORT": "tcp",
    "MQTT_USE_TLS": "false",
    "MQTT_USER": "lemari-1",
    "MQTT_PASS": "lem1-IJjLZ7QCc2RI8UyC",
})

import paho.mqtt.client as mqtt

connected = False

def on_connect(c, ud, flags, rc, props=None):
    global connected
    print(f"[on_connect] rc={rc} type={type(rc)}", flush=True)
    connected = (rc == 0)
    if connected:
        print("[on_connect] SUCCESS! Subscribing...", flush=True)
        result = c.subscribe("tetasco/lemari-1/command/#", qos=1)
        print(f"[on_connect] subscribe result: {result}", flush=True)
    else:
        print(f"[on_connect] FAILED rc={rc}", flush=True)

def on_disconnect(c, ud, flags, rc, props=None):
    print(f"[on_disconnect] rc={rc}", flush=True)

def on_log(c, ud, level, buf):
    if level <= 16:  # hanya DEBUG+INFO
        print(f"PAHO: {buf}", flush=True)

client = mqtt.Client(
    client_id="lemari-1-test",
    transport="tcp",
    protocol=mqtt.MQTTv5,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
)
client.username_pw_set("lemari-1", "lem1-IJjLZ7QCc2RI8UyC")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_log = on_log

print("Connecting via TCP to 192.168.1.14:1883...", flush=True)
try:
    client.connect("192.168.1.14", 1883, 60)
    print("connect() returned! Starting loop...", flush=True)
    client.loop_start()
    time.sleep(8)
    print(f"After 8s: connected={connected}", flush=True)
    client.loop_stop()
    client.disconnect()
except Exception as e:
    import traceback; traceback.print_exc()

print("Test done!", flush=True)
PYEOF
''', 'Test MQTT verbose di lemari-1')

cl.close()
print('\nDone!', flush=True)
