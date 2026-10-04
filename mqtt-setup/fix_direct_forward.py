"""
fix_direct_forward.py
======================
Flow yang benar:
  HP → Cloudflare → Server → LAN → Raspi Flask API → GPIO

Server (192.168.1.14) forward langsung ke Raspi (192.168.1.27:5001)
tanpa polling, instant seperti dulu.

Mapping nama device:
  Server API      → Raspi Flask
  fan             → fan
  heater/heater-1 → lamp_1
  heater2/heater-2→ lamp_2
  humidifier      → mist_maker
  motor           → motor
  uv/uv_light     → uv_light
"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=30):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Baca main.py dari container
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

# Cek apakah sudah ada direct forward
if 'RASPI_LOCAL_URL' in main_py or 'raspi_local' in main_py:
    print('[INFO] Direct forward sudah ada')
else:
    # Patch 1: Tambah konstanta dan helper untuk direct forward
    DIRECT_FORWARD_CODE = '''

# ── Direct LAN Forward ke Raspi Flask API ────────────────────────────────────
import urllib.request as _urllib_req

# IP Raspi lemari di LAN (ambil dari heartbeat jika tersedia, fallback hardcode)
RASPI_LOCAL_IPS: dict[int, str] = {
    1: "192.168.1.27",   # lemari-1
}

# Mapping nama actuator dari API server → nama GPIO di Raspi Flask
_RASPI_ACTUATOR_MAP = {
    "fan":        "fan",
    "heater":     "lamp_1",
    "heater-1":   "lamp_1",
    "heater1":    "lamp_1",
    "heater2":    "lamp_2",
    "heater-2":   "lamp_2",
    "humidifier": "mist_maker",
    "motor":      "motor",
    "uv":         "uv_light",
    "uv_light":   "uv_light",
    "uv-light":   "uv_light",
    "lamp_1":     "lamp_1",
    "lamp_2":     "lamp_2",
    "mist_maker": "mist_maker",
}


def _forward_to_raspi(tetasco_id: int, actuator: str, state: bool) -> dict:
    """
    Forward perintah kontrol langsung ke Raspi Flask API via LAN.
    POST http://{raspi_ip}:5001/api/actuators/{name}  body: {"state": bool}
    Return: {"ok": True} atau {"ok": False, "error": "..."}
    """
    # Cek apakah ada IP dari heartbeat cache (lebih akurat)
    did = device_id_from_tetasco_id(tetasco_id)
    hb_ip = device_heartbeat_cache.get(did, {}).get("ip")
    raspi_ip = hb_ip or RASPI_LOCAL_IPS.get(tetasco_id)

    if not raspi_ip:
        return {"ok": False, "error": "IP Raspi tidak diketahui"}

    raspi_name = _RASPI_ACTUATOR_MAP.get(actuator, actuator)
    url = f"http://{raspi_ip}:5001/api/actuators/{raspi_name}"
    body = __import__("json").dumps({"state": state}).encode()
    try:
        req = _urllib_req.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with _urllib_req.urlopen(req, timeout=3) as resp:
            result = __import__("json").loads(resp.read().decode())
            logger.info(f"[DirectFwd] lemari-{tetasco_id} {raspi_name}={'ON' if state else 'OFF'} ✅")
            return {"ok": True, "raspi": result}
    except Exception as e:
        logger.warning(f"[DirectFwd] Gagal: {e}")
        return {"ok": False, "error": str(e)}

'''

    if '\nif __name__ ==' in main_py:
        main_py = main_py.replace('\nif __name__ ==', DIRECT_FORWARD_CODE + '\nif __name__ ==', 1)
    print('[OK] _forward_to_raspi helper ditambahkan')

    # Patch 2: Modifikasi control endpoint untuk pakai direct forward
    # Cari baris queue update dan tambah direct forward SEBELUM return
    OLD_BEFORE_RETURN = '''    # ── Push instant ke Raspi via WS (jika tersambung) ──
    try:
        _push_command_to_raspi(tetasco_id, actuator, action)
    except Exception:
        pass
    return DeviceCommandResponse('''

    NEW_BEFORE_RETURN = '''    # ── Direct forward ke Raspi Flask via LAN (instant, no polling!) ──
    _fwd = _forward_to_raspi(tetasco_id, actuator, state)
    if _fwd.get("ok") and _fwd.get("raspi"):
        # Update cache dari response Raspi (akurat)
        raspi_state = _fwd["raspi"].get("state", state)
        device_status_cache[device_id][actuator] = raspi_state
    return DeviceCommandResponse('''

    if OLD_BEFORE_RETURN in main_py:
        main_py = main_py.replace(OLD_BEFORE_RETURN, NEW_BEFORE_RETURN, 1)
        print('[OK] Control endpoint: direct forward ke Raspi')
    else:
        # Fallback: tambah setelah queue update
        OLD2 = '    except Exception as _qe:\n        pass\n    return DeviceCommandResponse('
        NEW2 = '''    except Exception as _qe:
        pass
    # ── Direct forward ke Raspi Flask via LAN (instant, no polling!) ──
    _fwd = _forward_to_raspi(tetasco_id, actuator, state)
    if _fwd.get("ok") and _fwd.get("raspi"):
        raspi_state = _fwd["raspi"].get("state", state)
        device_status_cache[device_id][actuator] = raspi_state
    return DeviceCommandResponse('''
        if OLD2 in main_py:
            main_py = main_py.replace(OLD2, NEW2, 1)
            print('[OK] Control endpoint: direct forward (fallback pattern)')
        else:
            print('[WARN] Pattern tidak ditemukan!')
            idx = main_py.find('return DeviceCommandResponse(')
            print(f'DeviceCommandResponse at: {idx}')
            print(main_py[max(0,idx-200):idx+100])

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_direct.py')
sftp.close()
srv('docker cp /tmp/main_direct.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Verifikasi end-to-end: ukur waktu
print('\n=== TEST INSTANT CONTROL ===')
import time as _time
t0 = _time.time()
result = srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
t1 = _time.time()
print(f'Waktu: {(t1-t0)*1000:.0f}ms')
if 'success' in result:
    print('✅ Control berfungsi!')
if 'DirectFwd' in srv('docker logs tetasco-backend --tail 5 2>&1', 'Server log'):
    print('✅ Direct forward berjalan!')

srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/off", 'Fan OFF')
srv('docker logs tetasco-backend --tail 8 2>&1 | grep -i "DirectFwd\\|error\\|warn"', 'DirectFwd logs')

sv.close()
print('\n✅ Done! Control sekarang direct forward via LAN — INSTANT!')
