import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def r(cmd, lbl='', t=30):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Baca main.py
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

# Cek apakah endpoint sudah ada
has_history = '/sensors/history' in main_py
has_pending = 'pending-commands' in main_py
has_devices_action = '/devices/{device_name}/{action}' in main_py
print(f'sensors/history: {has_history}, pending-commands: {has_pending}, devices/action: {has_devices_action}')

NEW_ENDPOINTS = '''

# ═══════════════════════════════════════════════════════════════════════════════
# RELAY ENDPOINTS — Raspi push sensor data + HP kontrol relay via polling
# ═══════════════════════════════════════════════════════════════════════════════
import time as _relay_time
from collections import deque

# In-memory: antrian command untuk setiap device
_command_queues: dict[int, deque] = {}   # tetasco_id → deque of commands

def _cmd_queue(tid: int) -> deque:
    if tid not in _command_queues:
        _command_queues[tid] = deque(maxlen=20)
    return _command_queues[tid]


class SensorPushBody(BaseModel):
    temperature: float
    humidity: float
    device_id: str | None = None
    ip: str | None = None


@app.post("/api/tetasco/{tetasco_id}/sensors/history")
async def push_sensor_history(tetasco_id: int, body: SensorPushBody, request: Request):
    """
    Raspi push sensor data tiap ~15 detik via cloud_sync.
    Update device_sensor_cache + heartbeat_cache.
    """
    did = device_id_from_tetasco_id(tetasco_id)
    now = int(_relay_time.time())

    # Update cache sensor
    device_sensor_cache[did] = {
        "temperature": body.temperature,
        "humidity":    body.humidity,
        "ts":          now,
        "online":      True,
    }

    # Update heartbeat cache sekaligus (push sensor = device hidup)
    device_heartbeat_cache[did] = {
        "ts":    now,
        "ip":    body.ip or request.client.host,
        "did":   did,
    }

    logger.info(f"[SensorPush] lemari-{tetasco_id}: T={body.temperature}°C H={body.humidity}%")
    return {"ok": True, "received": {"temperature": body.temperature, "humidity": body.humidity}}


@app.post("/api/tetasco/{tetasco_id}/devices/{device_name}/{action}")
async def control_device(tetasco_id: int, device_name: str, action: str):
    """
    HP kirim command ON/OFF ke relay.
    Command di-queue, Raspi poll via /pending-commands.
    """
    if action not in ("on", "off"):
        raise HTTPException(status_code=400, detail="Action harus on/off")
    cmd = {"device": device_name, "action": action, "ts": int(_relay_time.time())}
    _cmd_queue(tetasco_id).appendleft(cmd)
    logger.info(f"[Control] Queue: lemari-{tetasco_id} → {device_name}={action}")
    return {"ok": True, "queued": cmd}


@app.get("/api/tetasco/{tetasco_id}/pending-commands")
async def get_pending_commands(tetasco_id: int):
    """
    Raspi poll tiap ~3 detik untuk dapat command dari HP.
    Command langsung di-clear setelah diambil.
    """
    q = _cmd_queue(tetasco_id)
    cmds = list(q)
    q.clear()
    return {"commands": cmds}


# Override endpoint sensor GET agar pakai cache baru
@app.get("/api/tetasco/{tetasco_id}/sensor")
async def get_sensor_data_v2(tetasco_id: int):
    """
    Return sensor terbaru dari cache (diisi oleh SensorPush dari Raspi).
    """
    did = device_id_from_tetasco_id(tetasco_id)
    hb  = device_heartbeat_cache.get(did, {})
    s   = device_sensor_cache.get(did, {})
    now = int(_relay_time.time())
    online = bool(hb.get("ts") and (now - hb["ts"]) < 120)
    if not online:
        return {
            "device_id": did, "tetasco_id": tetasco_id,
            "online": False, "temperature": None, "humidity": None,
            "message": "Raspi tidak mengirim data. Pastikan terhubung ke internet."
        }
    return {
        "device_id":   did,
        "tetasco_id":  tetasco_id,
        "online":      True,
        "temperature": s.get("temperature"),
        "humidity":    s.get("humidity"),
        "last_updated": hb.get("ts"),
    }

'''

if has_history and has_pending and has_devices_action:
    print('[INFO] Semua endpoint sudah ada')
else:
    # Tambahkan sebelum baris if __name__
    if 'if __name__ ==' in main_py:
        main_py = main_py.replace(
            '\nif __name__ ==',
            NEW_ENDPOINTS + '\nif __name__ ==',
            1
        )
    else:
        main_py = main_py.rstrip() + NEW_ENDPOINTS

    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.close()
    print('[OK] Endpoints baru ditambahkan')

# Copy ke container dan restart
sftp2 = sv.open_sftp()
sftp2.putfo(io.BytesIO(main_py.encode()), '/tmp/main_new.py')
sftp2.close()
r('docker cp /tmp/main_new.py tetasco-backend:/app/main.py && echo copied', '1. Copy ke container')
r('docker restart tetasco-backend 2>&1 | tail -1', '2. Restart', t=20)
time.sleep(10)
r('curl -s http://localhost:8000/api/health', '3. Health')

# Test endpoint baru
r("curl -s -X POST http://localhost:8000/api/tetasco/1/sensors/history -H 'Content-Type: application/json' -d '{\"temperature\":37.5,\"humidity\":60.0}'", '4. Test push sensor')
time.sleep(1)
r('curl -s http://localhost:8000/api/tetasco/1/sensor', '5. Sensor setelah push')
r("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", '6. Test control fan ON')
r('curl -s http://localhost:8000/api/tetasco/1/pending-commands', '7. Pending commands')

sv.close()
print('\n✅ Done!')
