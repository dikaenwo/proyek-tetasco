"""deploy_sensor_update.py — Update mqtt_bridge di lemari-1 + tambah endpoint sensor di server"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Koneksi ────────────────────────────────────────────────────────────────────
c_lemari = paramiko.SSHClient()
c_lemari.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c_lemari.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

c_server = paramiko.SSHClient()
c_server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c_server.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

LEMARI_PROJ = '/home/tetasco1/Penetas-Telur/backend'
SERVER_PROJ = '/home/telur/tetasco-connect/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(60)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# ── 1. Upload mqtt_bridge.py ke lemari-1 ──────────────────────────────────────
sftp = c_lemari.open_sftp()
sftp.put(
    r'd:\Proyek Penetas Telur\mqtt-setup\raspberry_pi\mqtt_bridge.py',
    f'{LEMARI_PROJ}/hardware/mqtt_bridge.py'
)
sftp.close()
print('[OK] mqtt_bridge.py uploaded to lemari-1', flush=True)

# ── 2. Tambah endpoint sensor di FastAPI server ────────────────────────────────
# Patch main.py: tambahkan GET endpoints sensor setelah mqtt_status endpoint
SENSOR_ENDPOINTS = '''

# ─── Endpoint Sensor Data (dari MQTT cache) ────────────────────────────────────

@app.get("/api/tetasco/{tetasco_id}/sensor")
def get_device_sensor(tetasco_id: int):
    """Ambil data suhu & kelembaban terbaru dari lemari (update real-time via MQTT)."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    data = device_sensor_cache.get(device_id)
    if not data:
        return {
            "device_id":   device_id,
            "tetasco_id":  tetasco_id,
            "online":      False,
            "temperature": None,
            "humidity":    None,
            "message":     "Belum ada data sensor. Pastikan Raspi lemari terhubung via MQTT."
        }
    return {
        "device_id":    device_id,
        "tetasco_id":   tetasco_id,
        "online":       True,
        "temperature":  data.get("temperature"),
        "humidity":     data.get("humidity"),
        "sensor_type":  data.get("sensor_type",   "unknown"),
        "is_hardware":  data.get("is_hardware",   False),
        "sensor_status":data.get("sensor_status", "unknown"),
        "actuators":    data.get("actuators",     {}),
        "ts":           data.get("ts"),
        "last_updated": data.get("ts"),
    }


@app.get("/api/sensors")
def get_all_sensors():
    """Ambil data sensor semua lemari yang sedang online via MQTT."""
    result = []
    for device_id, data in device_sensor_cache.items():
        # Parse nomor lemari dari device_id (misal: "lemari-1" → 1)
        try:
            tetasco_id = int(device_id.split("-")[-1])
        except Exception:
            tetasco_id = None
        result.append({
            "device_id":    device_id,
            "tetasco_id":   tetasco_id,
            "online":       True,
            "temperature":  data.get("temperature"),
            "humidity":     data.get("humidity"),
            "sensor_type":  data.get("sensor_type",   "unknown"),
            "is_hardware":  data.get("is_hardware",   False),
            "sensor_status":data.get("sensor_status", "unknown"),
            "actuators":    data.get("actuators",     {}),
            "ts":           data.get("ts"),
        })
    return {
        "total_online": len(result),
        "sensors": sorted(result, key=lambda x: x.get("tetasco_id") or 99),
    }


@app.get("/api/tetasco/{tetasco_id}/status")
def get_device_status(tetasco_id: int):
    """Ambil status aktuator terbaru dari lemari (dari MQTT cache)."""
    device_id = device_id_from_tetasco_id(tetasco_id)
    heartbeat  = device_heartbeat_cache.get(device_id, {})
    status     = device_status_cache.get(device_id, {})
    sensor     = device_sensor_cache.get(device_id, {})
    return {
        "device_id":   device_id,
        "tetasco_id":  tetasco_id,
        "online":      bool(heartbeat),
        "last_seen":   heartbeat.get("ts"),
        "ip":          heartbeat.get("ip"),
        "actuators":   status,
        "sensor": {
            "temperature":  sensor.get("temperature"),
            "humidity":     sensor.get("humidity"),
            "sensor_type":  sensor.get("sensor_type"),
            "is_hardware":  sensor.get("is_hardware"),
        } if sensor else None,
    }


@app.get("/api/devices")
def get_all_devices():
    """Rangkuman semua lemari yang pernah terhubung."""
    all_ids = set(device_status_cache) | set(device_sensor_cache) | set(device_heartbeat_cache)
    result  = []
    for device_id in sorted(all_ids):
        try:
            tetasco_id = int(device_id.split("-")[-1])
        except Exception:
            tetasco_id = None
        hb = device_heartbeat_cache.get(device_id, {})
        s  = device_sensor_cache.get(device_id, {})
        result.append({
            "device_id":   device_id,
            "tetasco_id":  tetasco_id,
            "online":      bool(hb),
            "ip":          hb.get("ip"),
            "last_seen":   hb.get("ts"),
            "temperature": s.get("temperature"),
            "humidity":    s.get("humidity"),
            "sensor_type": s.get("sensor_type"),
        })
    return {"total": len(result), "devices": result}
'''

# Cek apakah endpoints sudah ada
r(c_server, f'grep -c "get_device_sensor\|get_all_sensors" {SERVER_PROJ}/main.py',
  '2. Cek endpoint sudah ada')

# Patch via Python script di server
PATCH = f"""
python3 << 'PYEOF'
content = open('{SERVER_PROJ}/main.py').read()
if 'get_device_sensor' in content:
    print('Endpoints sudah ada, skip.')
else:
    # Tambahkan sebelum baris terakhir / setelah endpoint terakhir
    content = content.rstrip() + {repr(SENSOR_ENDPOINTS)}
    open('{SERVER_PROJ}/main.py', 'w').write(content)
    print('Sensor endpoints added OK!')
PYEOF
"""
r(c_server, PATCH, '3. Patch FastAPI main.py')

# Restart backend server
r(c_server,
  'docker restart tetasco-backend && sleep 5 && '
  'docker logs tetasco-backend --tail=10 2>&1',
  '4. Restart server backend')

# ── 3. Restart lemari-1 backend ───────────────────────────────────────────────
r(c_lemari,
  f'pkill -f "python.*app.py" 2>/dev/null; sleep 2; '
  f'cd {LEMARI_PROJ} && set -a && source .env && set +a && '
  f'nohup python3 app.py >> app.log 2>&1 & echo "PID:$!"',
  '5. Restart lemari-1 backend')

time.sleep(8)
r(c_lemari, f'grep -i "MQTTBridge.*Sensor\|Sensor publish" {LEMARI_PROJ}/app.log | tail -5', '6. Sensor log lemari-1')

# ── 4. Test endpoint sensor ────────────────────────────────────────────────────
time.sleep(5)
r(c_server, 'curl -s http://localhost:8000/api/tetasco/1/sensor | python3 -m json.tool', '7. GET /api/tetasco/1/sensor')
r(c_server, 'curl -s http://localhost:8000/api/sensors | python3 -m json.tool', '8. GET /api/sensors (semua lemari)')

c_lemari.close()
c_server.close()
print('\nDone!', flush=True)
