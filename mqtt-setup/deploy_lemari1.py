"""deploy_lemari1.py — Deploy mqtt_bridge.py ke lemari-1 dan patch app.py"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = 'tetasco1'
USER = 'tetasco1'
PASS = 'saumata1192'
PROJ = '/home/tetasco1/Penetas-Telur/backend'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASS, timeout=10)
print(f'Connected to {HOST}!', flush=True)

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(120)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# 1. Install paho-mqtt
r('pip3 install "paho-mqtt>=2.0.0" --quiet && python3 -c "import paho.mqtt; print(\'paho-mqtt OK:\', paho.mqtt.__version__)"',
  '1. Install paho-mqtt')

# 2. Upload mqtt_bridge.py ke folder hardware/
LOCAL_BRIDGE = r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py'
sftp = c.open_sftp()
sftp.put(LOCAL_BRIDGE, f'{PROJ}/hardware/mqtt_bridge.py')
print(f'\n[2. Upload] mqtt_bridge.py → {PROJ}/hardware/mqtt_bridge.py', flush=True)

# 3. Buat .env file dengan credentials lemari-1
ENV_CONTENT = (
    'DEVICE_ID=lemari-1\n'
    'MQTT_BROKER=tetasco.my.id\n'
    'MQTT_PORT=443\n'
    'MQTT_TRANSPORT=websockets\n'
    'MQTT_USE_TLS=true\n'
    'MQTT_WEBSOCKET_PATH=/mqtt\n'
    'MQTT_USER=lemari-1\n'
    'MQTT_PASS=lem1-IJjLZ7QCc2RI8UyC\n'
    'SENSOR_INTERVAL=15\n'
    'HEARTBEAT_INTERVAL=30\n'
)
sftp.putfo(io.BytesIO(ENV_CONTENT.encode()), f'{PROJ}/.env')
print(f'[2. Upload] .env → {PROJ}/.env', flush=True)
sftp.close()

# 4. Cek apakah app.py sudah ada patch mqtt_bridge
r(f'grep -n "mqtt_bridge" {PROJ}/app.py | head -5', '3. Cek patch mqtt_bridge di app.py')

# 5. Cek akhir file app.py untuk tau dimana inject
r(f'tail -30 {PROJ}/app.py', '4. Tail app.py')

# 6. Test import mqtt_bridge standalone
r(f'cd {PROJ} && DEVICE_ID=lemari-1 MQTT_PASS=lem1-IJjLZ7QCc2RI8UyC '
  f'python3 -c "from hardware.mqtt_bridge import mqtt_bridge; print(\'Import OK\'); '
  f'print(\'DEVICE_ID:\', mqtt_bridge._gpio)"',
  '5. Test import mqtt_bridge')

c.close()
print('\nDone!', flush=True)
