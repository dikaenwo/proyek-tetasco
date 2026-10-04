"""verify_mqtt_lemari1.py — Verifikasi MQTT bridge lemari-1 dan test end-to-end"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- Lemari-1 ---
c1 = paramiko.SSHClient()
c1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c1.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

# --- Server Pusat ---
cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8','replace').strip()
    print(out if out else '(empty)', flush=True)
    return out

# 1. Cek log MQTT bridge di lemari-1
r(c1, 'grep -i "MQTTBridge\|MQTT Bridge\|paho\|mqtt" /home/tetasco1/Penetas-Telur/backend/app.log | tail -20',
  '1. MQTT log di lemari-1')

# 2. Cek apakah paho-mqtt installed
r(c1, 'python3 -c "import paho.mqtt.client as m; print(\'paho OK:\', m.__version__)" 2>&1',
  '2. Paho-mqtt status')

# 3. Test dari server: publish command ke lemari-1 via MQTT
print('\n[3. Test: Server kirim command fan ON ke lemari-1]', flush=True)
r(cs,
  'docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/lemari-1/command/fan" '
  '-m \'{"state":true}\' && echo "Command published!"',
  '3a. Publish dari server')

time.sleep(3)

# 4. Cek log lemari-1 setelah command
r(c1, 'tail -15 /home/tetasco1/Penetas-Telur/backend/app.log', '4. Log lemari-1 setelah command')

# 5. Cek state fan via REST API lokal lemari-1
r(c1, 'curl -s http://localhost:5001/api/actuators | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'fan:\', d.get(\'fan\',d))"',
  '5. Status aktuator lemari-1')

# 6. Kirim fan OFF
r(cs,
  'docker exec tetasco-mosquitto mosquitto_pub '
  '-h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" '
  '-t "tetasco/lemari-1/command/fan" '
  '-m \'{"state":false}\' && echo "Fan OFF published!"',
  '6. Publish fan OFF')

time.sleep(2)
r(c1, 'curl -s http://localhost:5001/api/actuators | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))"',
  '7. Final aktuator state')

c1.close()
cs.close()
print('\nVerification done!', flush=True)
