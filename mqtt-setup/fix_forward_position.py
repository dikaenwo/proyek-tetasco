import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

# Cek struktur file akhir (tidak ada if __name__)
has_main = 'if __name__ ==' in main_py
print(f'has __main__: {has_main}')

# Hapus semua sisa patch yang salah (fungsi yang ter-insert di akhir file atau tidak terdefinisi)
# Cari dan hapus blok _forward_to_raspi yang mungkin ter-insert di tempat salah
if '# ── Direct LAN Forward ke Raspi Flask API ─' in main_py:
    # Hapus dari tanda komentar sampai akhir definisi fungsi
    start_marker = '\n# ── Direct LAN Forward ke Raspi Flask API ─'
    end_marker = '_RASPI_ACTUATOR_MAP = {'
    idx_start = main_py.find(start_marker)
    # Cari akhir fungsi (sampai baris kosong ganda setelah def)
    # Temukan penutup dengan mencari definisi berikutnya atau EOF
    if idx_start > 0:
        # Hapus blok ini (sudah ada di tempat salah)
        idx_end = main_py.find('\n\n\n', idx_start + 50)
        if idx_end < 0:
            idx_end = len(main_py)
        else:
            idx_end += 3  # include triple newline
        removed = main_py[idx_start:idx_end]
        main_py = main_py[:idx_start] + main_py[idx_end:]
        print(f'[OK] Blok salah dihapus ({len(removed)} chars)')

# Juga hapus _raspi_ws_clients dan _push_command_to_raspi yang salah posisi
for bad_marker in ['\n# ── Raspi WebSocket Command Push ─', '\n# ── Direct forward ke Raspi Flask via LAN (instant, no polling!) ──\n    _fwd = _forward_to_raspi']:
    if bad_marker in main_py:
        idx = main_py.find(bad_marker)
        idx_end = main_py.find('\n\n\n', idx + 50)
        if idx_end < 0: idx_end = len(main_py)
        main_py = main_py[:idx] + main_py[idx_end:]
        print(f'[OK] Blok "{bad_marker[:30]}" dihapus')

# Sekarang sisipkan di tempat yang BENAR: tepat sebelum definisi control_device
DIRECT_FORWARD_CODE = '''
# ── Direct LAN Forward ke Raspi Flask API ────────────────────────────────────
import urllib.request as _urllib_req, json as _json_fwd

RASPI_LOCAL_IPS: dict = {1: "192.168.1.27"}

_RASPI_ACTUATOR_MAP = {
    "fan": "fan", "heater": "lamp_1", "heater-1": "lamp_1",
    "heater1": "lamp_1", "heater2": "lamp_2", "heater-2": "lamp_2",
    "humidifier": "mist_maker", "motor": "motor",
    "uv": "uv_light", "uv_light": "uv_light", "uv-light": "uv_light",
    "lamp_1": "lamp_1", "lamp_2": "lamp_2", "mist_maker": "mist_maker",
}

def _forward_to_raspi(tetasco_id: int, actuator: str, state: bool) -> dict:
    """Forward ke Raspi Flask API via LAN — instant, no polling."""
    did = device_id_from_tetasco_id(tetasco_id)
    raspi_ip = device_heartbeat_cache.get(did, {}).get("ip") or RASPI_LOCAL_IPS.get(tetasco_id)
    if not raspi_ip:
        return {"ok": False, "error": "IP Raspi tidak diketahui"}
    raspi_name = _RASPI_ACTUATOR_MAP.get(actuator, actuator)
    url = f"http://{raspi_ip}:5001/api/actuators/{raspi_name}"
    body = _json_fwd.dumps({"state": state}).encode()
    try:
        req = _urllib_req.Request(url, data=body,
              headers={"Content-Type": "application/json"}, method="POST")
        with _urllib_req.urlopen(req, timeout=3) as resp:
            result = _json_fwd.loads(resp.read().decode())
            logger.info(f"[DirectFwd] {raspi_name}={'ON' if state else 'OFF'} ✅")
            return {"ok": True, "raspi": result}
    except Exception as e:
        logger.warning(f"[DirectFwd] Gagal: {e}")
        return {"ok": False, "error": str(e)}

'''

# Sisipkan tepat sebelum "# ─── Endpoint Kontrol Perangkat"
CONTROL_SECTION = '# ─── Endpoint Kontrol Perangkat (dengan MQTT) ─'
if CONTROL_SECTION in main_py:
    main_py = main_py.replace(CONTROL_SECTION, DIRECT_FORWARD_CODE + CONTROL_SECTION, 1)
    print('[OK] _forward_to_raspi disisipkan SEBELUM control endpoint')
else:
    # Fallback: sebelum @app.post di line 127
    OLD_DECO = '@app.post("/api/tetasco/{tetasco_id}/devices/{actuator}/{action}")'
    if OLD_DECO in main_py:
        main_py = main_py.replace(OLD_DECO, DIRECT_FORWARD_CODE.rstrip() + '\n\n' + OLD_DECO, 1)
        print('[OK] Disisipkan sebelum control endpoint decorator')

# Fix control endpoint: ganti _forward_to_raspi yang mungkin masih ada atau tambahkan
OLD_RETURN = '''    except Exception as _qe:
        pass
    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        actuator=actuator,
        state=state,
        mqtt_sent=mqtt_sent,
        message=f"{actuator.upper()} {'ON' if state else 'OFF'} \u2014 perintah dikirim ke {device_id}",
    )'''

NEW_RETURN = '''    except Exception as _qe:
        pass
    # ── Direct forward ke Raspi via LAN (instant!) ──
    _fwd = _forward_to_raspi(tetasco_id, actuator, state)
    if _fwd.get("ok") and _fwd.get("raspi"):
        device_status_cache[device_id][actuator] = _fwd["raspi"].get("state", state)
    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        actuator=actuator,
        state=state,
        mqtt_sent=_fwd.get("ok", mqtt_sent),
        message=f"{actuator.upper()} {'ON' if state else 'OFF'} \u2014 {'GPIO OK' if _fwd.get('ok') else 'queued'}",
    )'''

if OLD_RETURN in main_py:
    main_py = main_py.replace(OLD_RETURN, NEW_RETURN, 1)
    print('[OK] Return DeviceCommandResponse diupdate dengan direct forward')

# Verifikasi posisi fungsi
idx = main_py.find('def _forward_to_raspi')
idx_ctrl = main_py.find('def control_device')
print(f'_forward_to_raspi at idx: {idx}, control_device at: {idx_ctrl}')
print(f'Order benar: {idx < idx_ctrl}')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_final.py')
sftp.close()
srv('docker cp /tmp/main_final.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Test
result = srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
if '"success":true' in result:
    print('\n✅ Control berfungsi!')
else:
    srv('docker logs tetasco-backend --tail 10 2>&1', 'Error log')

time.sleep(0.5)
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/off", 'Fan OFF')
srv('docker logs tetasco-backend --tail 5 2>&1 | grep -i "DirectFwd\\|error\\|NameError"', 'DirectFwd log')

sv.close()
print('\n✅ Done!')
