"""
fix_instant_control.py
========================
Ganti polling 5 detik → push command lewat WebSocket camera (instant!)

Plan:
1. SERVER: Simpan WebSocket Raspi saat connect, push command JSON saat HP kirim
2. RASPI: Tambah receive thread di camera WS connection, eksekusi GPIO langsung
3. RASPI: Kurangi poll interval ke 1 detik sebagai fallback
"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras_bg(cmd):
    transport = rp.get_transport()
    chan = transport.open_session()
    chan.exec_command(cmd)
    time.sleep(0.5)
    chan.close()

# ══════════════════════════════════════════════════════════════
# 1. SERVER: Patch camera WS handler untuk push command
# ══════════════════════════════════════════════════════════════
print('=== PATCH SERVER ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

# Cari camera WebSocket handler
cam_push_idx = main_py.find('/camera/push')
if cam_push_idx > 0:
    # Tampilkan context
    ctx_start = max(0, cam_push_idx - 100)
    ctx_end = min(len(main_py), cam_push_idx + 800)
    print('\n[Camera WS handler context]:')
    print(main_py[ctx_start:ctx_end])

# Tambah dict untuk simpan Raspi WS connection
if '_raspi_ws' not in main_py:
    # Tambah storage + modifikasi control endpoint untuk push ke WS
    SERVER_WS_PATCH = '''

# ── Raspi WebSocket Command Push ─────────────────────────────────────────────
import json as _json
_raspi_ws_clients: dict[int, object] = {}   # tetasco_id → WebSocket object

def _push_command_to_raspi(tetasco_id: int, device: str, action: str):
    """Push command langsung ke Raspi via existing camera WebSocket (instant!)."""
    ws = _raspi_ws_clients.get(tetasco_id)
    if ws is None:
        return False
    try:
        msg = _json.dumps({"type": "command", "device": device, "action": action})
        ws.send_text(msg)
        logger.info(f"[WS-Push] Instant command: lemari-{tetasco_id} → {device}={action}")
        return True
    except Exception as e:
        logger.warning(f"[WS-Push] Gagal push ke Raspi {tetasco_id}: {e}")
        _raspi_ws_clients.pop(tetasco_id, None)
        return False

'''
    # Sisipkan sebelum if __name__
    if '\nif __name__ ==' in main_py:
        main_py = main_py.replace('\nif __name__ ==', SERVER_WS_PATCH + '\nif __name__ ==', 1)
    print('[OK] _raspi_ws_clients storage ditambahkan')

    # Patch camera push WebSocket handler untuk simpan koneksi
    # Cari WebSocket endpoint camera
    cam_endpoint = '@app.websocket("/api/tetasco/{tetasco_id}/camera/push")'
    if cam_endpoint in main_py:
        # Cari "await websocket.accept()" dan tambah storage setelahnya
        old_accept = 'await websocket.accept()'
        if old_accept in main_py:
            # Cari instance pertama yang ada di camera push handler
            cam_handler_start = main_py.find(cam_endpoint)
            accept_after_cam = main_py.find(old_accept, cam_handler_start)
            if accept_after_cam > 0:
                main_py = (
                    main_py[:accept_after_cam + len(old_accept)] +
                    '\n    _raspi_ws_clients[tetasco_id] = websocket  # Simpan untuk push command' +
                    main_py[accept_after_cam + len(old_accept):]
                )
                print('[OK] Camera WS handler: simpan koneksi Raspi')

    # Patch control endpoint untuk push instant via WS setelah queue
    old_queue_done = '    except Exception as _qe:\n        pass\n    return DeviceCommandResponse('
    new_queue_done = '''    except Exception as _qe:
        pass
    # ── Push instant ke Raspi via WS (jika tersambung) ──
    try:
        _push_command_to_raspi(tetasco_id, actuator, action)
    except Exception:
        pass
    return DeviceCommandResponse('''
    if old_queue_done in main_py:
        main_py = main_py.replace(old_queue_done, new_queue_done, 1)
        print('[OK] Control endpoint: tambah instant WS push')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_ws.py')
sftp.close()
srv('docker cp /tmp/main_ws.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# ══════════════════════════════════════════════════════════════
# 2. RASPI: Tambah receive thread di camera WS
# ══════════════════════════════════════════════════════════════
print('\n=== PATCH RASPI app.py ===')
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')
print(f'app.py: {len(app_py)} chars')

if 'ws_receive_thread' in app_py or 'recv_command' in app_py:
    print('[INFO] Receive thread sudah ada')
else:
    OLD_CAM_LOOP = '''            while True:
                if not cap.grab():
                    _t.sleep(0.05); continue
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    continue
                ok, buf = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    ws.send_binary(buf.tobytes())
                _t.sleep(0.05)  # ~20 FPS'''

    NEW_CAM_LOOP = '''            # Thread terpisah untuk receive command dari server
            import threading as _thr, json as _json_cmd

            def _recv_commands():
                """Terima command JSON dari server dan eksekusi GPIO."""
                while True:
                    try:
                        msg = ws.recv()
                        if isinstance(msg, str) and msg.strip():
                            try:
                                data = _json_cmd.loads(msg)
                                if data.get('type') == 'command':
                                    dev    = data.get('device')
                                    action = data.get('action')
                                    if dev and action in ('on', 'off'):
                                        state = (action == 'on')
                                        gpio_controller.set_actuator(dev, state)
                                        logger.info(f"[WS-CMD] Instant: {dev}={action}")
                            except Exception as _pe:
                                logger.debug(f"[WS-CMD] Parse error: {_pe}")
                    except Exception:
                        break  # WS closed, outer loop akan reconnect

            _recv_t = _thr.Thread(target=_recv_commands, daemon=True)
            _recv_t.start()

            while True:
                if not cap.grab():
                    _t.sleep(0.05); continue
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    continue
                ok, buf = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    ws.send_binary(buf.tobytes())
                _t.sleep(0.05)  # ~20 FPS'''

    if OLD_CAM_LOOP in app_py:
        app_py = app_py.replace(OLD_CAM_LOOP, NEW_CAM_LOOP, 1)
        print('[OK] Raspi camera loop: receive thread ditambahkan')
    else:
        print('[WARN] Camera loop pattern tidak ditemukan!')
        # Tampilkan konteks
        idx = app_py.find('while True:\n                if not cap.grab()')
        if idx > 0:
            print(app_py[max(0,idx-50):idx+300])

# 3. Kurangi poll interval ke 1 detik (fallback)
import json
cfg_json = json.dumps({
    "cloud_base_url": "http://192.168.1.14:8000",
    "tetasco_id": 1,
    "sync_interval_seconds": 1,   # ← 1 detik fallback
    "sync_devices_from_cloud": True
}, indent=2)
sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp2.putfo(io.BytesIO(cfg_json.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_config.json')
sftp2.close()
print('[OK] app.py di-update + poll interval → 1 detik')

# Restart Raspi app.py
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo ok', 'Kill old')
ras_bg('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Raspi restarted')
time.sleep(8)
ras('pgrep -fa "python3 backend/app.py" | head -1', 'Process check')

# Verifikasi
time.sleep(12)
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor (harus online)')
print('\n✅ Done! Kontrol sekarang instant via WS + 1 detik fallback poll')

sv.close()
rp.close()
