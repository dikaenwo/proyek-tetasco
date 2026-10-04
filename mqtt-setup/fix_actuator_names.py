import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek set_actuator implementation di gpio_controller
ras("sed -n '68,115p' ~/Penetas-Telur/backend/hardware/gpio_controller.py", 'set_actuator impl')

# Baca mqtt_subscriber.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/mqtt_subscriber.py')
mqtt_sub = o.read().decode('utf-8','replace')
print(f'\n[mqtt_subscriber.py]:\n{mqtt_sub}')

# Fix: tambah ACTUATOR_NAME_MAP di mqtt_subscriber.py
OLD_MSG = '''def _on_message(client, userdata, msg):
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
            logger.info(f"[MQTT-Cmd] INSTANT: {actuator}={'ON' if state else 'OFF'}")'''

NEW_MSG = '''# Mapping nama API server → nama GPIO controller Raspi
_ACTUATOR_MAP = {
    "humidifier":  "mist_maker",   # API: humidifier → GPIO: mist_maker
    "heater":      "lamp_1",       # API: heater     → GPIO: lamp_1
    "heater-1":    "lamp_1",
    "heater1":     "lamp_1",
    "heater-2":    "lamp_2",
    "heater2":     "lamp_2",
    "uv":          "uv_light",
    "uv-light":    "uv_light",
    # fan, motor, lamp_1, lamp_2, mist_maker → sudah benar
}

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
            # Map nama API → nama GPIO
            gpio_name = _ACTUATOR_MAP.get(actuator, actuator)
            _gpio.set_actuator(gpio_name, state)
            logger.info(f"[MQTT-Cmd] INSTANT: {actuator}({gpio_name})={'ON' if state else 'OFF'}")'''

if OLD_MSG in mqtt_sub:
    mqtt_sub = mqtt_sub.replace(OLD_MSG, NEW_MSG, 1)
    print('[OK] ACTUATOR_MAP ditambahkan ke mqtt_subscriber.py')
else:
    print('[WARN] Pattern tidak cocok')
    print(mqtt_sub[:300])

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(mqtt_sub.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/mqtt_subscriber.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/mqtt_subscriber.py && echo OK', 'Syntax check')

# Restart Raspi
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && > /tmp/tetasco_backend.log && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
time.sleep(10)
ras('ss -tnp | grep 1883 | head -1', 'MQTT connected')

# Test: humidifier OFF via MQTT langsung
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

print('\n=== Test humidifier OFF via MQTT ===')
i2,o2,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/on')
o2.read()
time.sleep(1)
i3,o3,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/off')
o3.read()
time.sleep(1)
ras('tail -5 /tmp/tetasco_backend.log | grep -i "INSTANT\\|GPIO"', 'GPIO log (harus mist_maker=OFF)')
ras("curl -s http://localhost:5001/api/actuators | python3 -c \"import sys,json;d=json.load(sys.stdin);print('fan:',d.get('fan'),'mist_maker:',d.get('mist_maker'))\"", 'State final')

sv.close()
rp.close()
print('\n✅ Name mapping fix selesai!')
