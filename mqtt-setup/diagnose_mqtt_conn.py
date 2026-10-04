"""diagnose_mqtt_conn.py — Diagnosa kenapa lemari-1 tidak bisa connect ke MQTT"""
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
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Cek versi paho di lemari-1
r(cl, '''python3 -c "
import paho
import paho.mqtt.client as m
print('paho package version:', paho.__version__ if hasattr(paho,'__version__') else 'unknown')
try:
    print('CallbackAPIVersion:', m.CallbackAPIVersion.VERSION2)
except:
    print('WARNING: CallbackAPIVersion.VERSION2 tidak ada! Paho < 2.0!')
print('Has VERSION2:', hasattr(m, 'CallbackAPIVersion'))
"''', '1. Cek paho version lemari-1')

# 2. Test TCP direct ke server (port 1883 dalam jaringan lokal)
r(cl, 'nc -z -w 3 192.168.1.14 1883 && echo "TCP 1883 OK" || echo "TCP 1883 FAIL"', '2. Test TCP port 1883')

# 3. Test koneksi MQTT TCP langsung (lebih simple, no WebSocket/TLS)
r(cl, '''python3 -c "
import paho.mqtt.client as m, time, sys

connected = False
def on_connect(c, ud, f, rc, *a):
    global connected
    connected = rc == 0
    print('on_connect rc:', rc, '|', 'OK' if rc==0 else 'FAIL')

try:
    c = m.Client(client_id='test-direct', protocol=m.MQTTv5,
                 callback_api_version=m.CallbackAPIVersion.VERSION2)
    c.username_pw_set('lemari-1', 'lem1-IJjLZ7QCc2RI8UyC')
    c.on_connect = on_connect
    c.connect('192.168.1.14', 1883, 10)
    c.loop_start()
    time.sleep(5)
    c.loop_stop()
    c.disconnect()
    print('MQTT TCP Direct:', 'CONNECTED!' if connected else 'FAILED')
except Exception as e:
    print('ERROR:', e)
"''', '3. Test MQTT TCP direct (lokal)')

# 4. Test WebSocket via tetasco.my.id
r(cl, '''timeout 15 python3 -c "
import paho.mqtt.client as m, time, ssl

connected = False
def on_connect(c, ud, f, rc, *a):
    global connected
    connected = rc == 0
    print('WS on_connect rc:', rc)
def on_log(c, ud, level, buf):
    print('LOG:', buf)

try:
    c = m.Client(client_id='"'"'test-ws'"'"', transport='"'"'websockets'"'"',
                 protocol=m.MQTTv5,
                 callback_api_version=m.CallbackAPIVersion.VERSION2)
    c.ws_set_options(path='"'"'/mqtt'"'"')
    c.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    c.username_pw_set('"'"'lemari-1'"'"', '"'"'lem1-IJjLZ7QCc2RI8UyC'"'"')
    c.on_connect = on_connect
    c.on_log = on_log
    c.connect_async('"'"'tetasco.my.id'"'"', 443, 30)
    c.loop_start()
    time.sleep(12)
    c.loop_stop()
    print('"'"'MQTT WSS:'"'"', '"'"'OK'"'"' if connected else '"'"'FAILED'"'"')
except Exception as e:
    print('"'"'ERROR:'"'"', e)
" 2>&1 | tail -20''', '4. Test MQTT WebSocket (internet)')

# 5. Cek nginx log untuk /mqtt requests
r(cs, 'docker logs tetasco-nginx --tail=20 2>&1 | grep mqtt', '5. Nginx /mqtt access log')

cl.close()
cs.close()
print('\nDiagnosa done!', flush=True)
