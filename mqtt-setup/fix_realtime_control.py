"""
fix_realtime_control.py
========================
Fix 3 hal:
1. SERVER: Tambah GET /api/tetasco/{id} → return actuator desired state
2. SERVER: POST devices/{device}/{action} juga simpan di _desired_state
3. RASPI: Enable sync_devices_from_cloud + tambah rapid poll pending-commands tiap 4 detik
"""
import paramiko, sys, io, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER: {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI: {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# ══════════════════════════════════════════════════════════════
# SERVER SIDE
# ══════════════════════════════════════════════════════════════
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'Server main.py: {len(main_py)} chars')

# Cek apakah endpoint /api/tetasco/{id} (GET) sudah ada
if '_desired_state' in main_py:
    print('[INFO] _desired_state sudah ada di server')
else:
    SERVER_PATCH = '''

# ── Desired State Store (untuk sync ke Raspi) ───────────────────────────────
_desired_state: dict[int, dict] = {}  # tetasco_id → {fan: bool, heater_1: bool, ...}

# Mapping nama device HP → nama lokal Raspi
_DEV_MAP = {
    "fan": "fan",
    "heater": "lamp_1",
    "heater-1": "lamp_1",
    "heater-2": "lamp_2",
    "humidifier": "mist_maker",
    "motor": "motor",
    "uv": "uv_light",
}


@app.get("/api/tetasco/{tetasco_id}")
async def get_tetasco_device(tetasco_id: int):
    """
    Raspi poll endpoint ini untuk sync desired state.
    Return: {fan: bool, heater_1: bool, humidifier: bool, ...}
    """
    did = device_id_from_tetasco_id(tetasco_id)
    hb  = device_heartbeat_cache.get(did, {})
    s   = device_sensor_cache.get(did, {})
    now = int(_relay_time.time())
    online = bool(hb.get("ts") and (now - hb["ts"]) < 120)
    ds = _desired_state.get(tetasco_id, {})
    return {
        "tetasco_id": tetasco_id,
        "device_id":  did,
        "online":     online,
        "temperature": s.get("temperature"),
        "humidity":    s.get("humidity"),
        # Desired actuator states (dikirim dari HP)
        "fan":         ds.get("fan"),
        "heater_1":    ds.get("lamp_1"),
        "heater_2":    ds.get("lamp_2"),
        "humidifier":  ds.get("mist_maker"),
        "motor":       ds.get("motor"),
    }

'''
    # Tambahkan patch sebelum if __name__
    if '\nif __name__ ==' in main_py:
        main_py = main_py.replace('\nif __name__ ==', SERVER_PATCH + '\nif __name__ ==', 1)
    else:
        main_py += SERVER_PATCH

    # Patch existing control endpoint to also store desired state
    # Cari endpoint yang sudah ada (fan/on via MQTT)
    OLD_CTRL = '@app.post("/api/tetasco/{tetasco_id}/devices/{device_name}/{action}")'
    if OLD_CTRL in main_py:
        # Tambah desired state update di awal handler
        # Cari baris setelah decorator
        idx = main_py.find(OLD_CTRL)
        # Cari body fungsi → tambah desired state update
        after_def = main_py.find('\n    ', idx + len(OLD_CTRL))
        insert_point = main_py.find('\n    ', after_def + 4)
        desired_update = '''
    # Update desired state (untuk Raspi polling)
    raspi_dev = _DEV_MAP.get(device_name, device_name)
    if tetasco_id not in _desired_state:
        _desired_state[tetasco_id] = {}
    _desired_state[tetasco_id][raspi_dev] = (action == "on")
    # Juga queue ke pending-commands
    _cmd_queue(tetasco_id).appendleft({"device": raspi_dev, "action": action, "ts": int(_relay_time.time())})
'''
        main_py = main_py[:insert_point] + desired_update + main_py[insert_point:]
        print('[OK] Control endpoint patched → store desired state + queue')
    else:
        print('[WARN] Control endpoint tidak ditemukan, skip patch')

    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_ctrl.py')
    sftp.close()
    print('[OK] Server main.py updated')

srv('docker cp /tmp/main_ctrl.py tetasco-backend:/app/main.py && echo ok', '1. Deploy ke container')
srv('docker restart tetasco-backend 2>&1 | tail -1', '2. Restart server', t=25)
time.sleep(10)
srv('curl -s http://localhost:8000/api/health', '3. Health')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", '4. Test fan ON → queue')
time.sleep(1)
srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', '5. Pending commands (harus ada fan)')
srv('curl -s http://localhost:8000/api/tetasco/1', '6. GET tetasco/1 (harus ada fan state)')

# ══════════════════════════════════════════════════════════════
# RASPI SIDE — Enable sync_devices_from_cloud + rapid poll
# ══════════════════════════════════════════════════════════════
print('\n\n=== RASPI SIDE ===')

# 1. Enable sync_devices_from_cloud di config
cfg_path = '~/Penetas-Telur/backend/hardware/cloud_config.json'
i,o,e = rp.exec_command(f'cat {cfg_path} 2>/dev/null || echo "{{}}"')
cfg_raw = o.read().decode('utf-8','replace').strip() or '{}'
try:
    cfg = json.loads(cfg_raw)
except:
    cfg = {}
cfg['sync_devices_from_cloud'] = True
cfg['sync_interval_seconds'] = 5  # Lebih cepat
cfg_json = json.dumps(cfg, indent=2)
sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(cfg_json.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_config.json')
sftp2.close()
print(f'[OK] cloud_config.json updated: {cfg_json}')

# 2. Tambah rapid poll pending-commands ke cloud_sync.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cs = o.read().decode('utf-8','replace')

if 'pending-commands' in cs:
    print('[INFO] pending-commands polling sudah ada')
else:
    # Tambah method poll_commands
    POLL_COMMANDS = '''
    def poll_and_execute_commands(self):
        """Fetch pending commands dari server dan eksekusi di GPIO lokal."""
        if not self.is_online or not self.gpio_controller:
            return
        tetasco_id = self.config.get("tetasco_id", 1)
        url = f"{self.config['cloud_base_url']}/api/tetasco/{tetasco_id}/pending-commands"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Tetasco-RPi-Client/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                cmds = data.get("commands", [])
                for cmd in cmds:
                    dev    = cmd.get("device")
                    action = cmd.get("action")
                    if dev and action in ("on", "off"):
                        state = (action == "on")
                        self.gpio_controller.set_actuator(dev, state)
                        logger.info(f"[CloudCtrl] Execute: {dev} → {action}")
        except Exception as e:
            logger.debug(f"[CloudCtrl] Poll error: {e}")

'''
    # Insert sebelum method _worker_loop
    cs = cs.replace('    def _worker_loop(self):', POLL_COMMANDS + '    def _worker_loop(self):', 1)

    # Tambah call ke poll_and_execute_commands di dalam _worker_loop, sebelum time.sleep
    cs = cs.replace(
        '            time.sleep(interval)',
        '            # Poll pending commands dari HP (fast control)\n            self.poll_and_execute_commands()\n            time.sleep(interval)',
        1
    )

    sftp2 = rp.open_sftp()
    sftp2.putfo(io.BytesIO(cs.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_sync.py')
    sftp2.close()
    print('[OK] cloud_sync.py: pending-commands polling ditambahkan')

# 3. Restart app.py Raspi
ras('kill $(pgrep -f "python3 backend/app.py") 2>/dev/null; sleep 2; nohup bash -lc "cd ~/Penetas-Telur && python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"; echo "restarted"', '3. Restart Raspi app.py', t=15)
time.sleep(8)
ras('tail -5 /tmp/tetasco_backend.log 2>/dev/null', '4. Raspi log')

# Verifikasi: apakah server sekarang terima sensor data?
time.sleep(10)
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', '5. Sensor di server setelah restart')

sv.close()
rp.close()
print('\n✅ Done! HP sekarang bisa kontrol relay & lihat sensor realtime.')
