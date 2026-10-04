"""debug_connection.py — Debug kenapa on_connect tidak terpanggil"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

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

PROJ = '/home/tetasco1/Penetas-Telur/backend'

# 1. Cek mosquitto log untuk koneksi dari 192.168.1.27
r(cs, 'docker logs tetasco-mosquitto --since=5m 2>&1 | grep -E "192.168.1.27|lemari|disconnect|auth|error" | tail -20',
  '1. Mosquitto log (filter lemari-1 IP)')

# 2. Cek apakah paho v2 on_connect signature sudah benar
r(cl, '''python3 << 'PYEOF'
import paho.mqtt.client as m, time, sys

connected = False
error = None

def on_connect(c, ud, flags, rc, props=None):
    global connected, error
    print(f"on_connect called! rc={rc}, type={type(rc)}")
    # paho v2: rc adalah ReasonCode object
    if hasattr(rc, "value"):
        ok = rc.value == 0
    else:
        ok = rc == 0
    connected = ok
    print(f"Connection: {'OK' if ok else 'FAIL'}")

def on_log(c, ud, level, buf):
    print(f"PAHO LOG [{level}]: {buf}")

try:
    c = m.Client(client_id="debug-direct", protocol=m.MQTTv5,
                 callback_api_version=m.CallbackAPIVersion.VERSION2)
    c.username_pw_set("lemari-1", "lem1-IJjLZ7QCc2RI8UyC")
    c.on_connect = on_connect
    c.on_log = on_log
    print("Connecting TCP to 192.168.1.14:1883...")
    c.connect_async("192.168.1.14", 1883, 30)
    c.loop_start()
    time.sleep(6)
    c.loop_stop()
    c.disconnect()
    print("Final:", "CONNECTED" if connected else "NOT CONNECTED")
except Exception as e:
    import traceback; traceback.print_exc()
PYEOF
''', '2. Test paho v2 on_connect (verbose)')

# 3. Cek app.log terbaru
r(cl, f'tail -30 {PROJ}/app.log', '3. app.log terbaru lemari-1')

cl.close()
cs.close()
print('\nDone!', flush=True)
