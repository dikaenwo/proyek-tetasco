"""
deploy_camera_relay.py
======================
1. Patch server FastAPI (main.py) — tambah WebSocket push + MJPEG stream endpoint
2. Patch Nginx config — streaming-friendly proxy untuk camera endpoint  
3. Patch Raspi backend (app.py) — WebSocket frame pusher ke server
4. Rebuild + restart docker di server
5. Restart Raspi backend
"""
import paramiko, sys, io, time, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── SSH helpers ──────────────────────────────────────────────────────────────
def ssh(host, user, pwd, timeout=10):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, 22, user, pwd, timeout=timeout)
    return c

def r(conn, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = conn.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

def upload(conn, content: str, remote_path: str):
    sftp = conn.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), remote_path)
    sftp.close()

# ─── 1. Connect ke kedua server ───────────────────────────────────────────────
print('=== Connecting ===')
sv = ssh('telur', 'telur', 'telur')
rs = ssh('192.168.1.27', 'tetasco1', 'saumata1192')
print('✅ Connected ke server (telur) dan Raspi (tetasco1)')

# ─── 2. Baca main.py dari server ──────────────────────────────────────────────
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'\n[INFO] main.py: {len(main_py)} chars')

# ─── 3. Tambah camera relay endpoints ke main.py ──────────────────────────────
CAMERA_ENDPOINTS = '''

# ═══════════════════════════════════════════════════════════════════════════════
# CAMERA RELAY — WebSocket push dari Raspi + MJPEG stream ke client
# ═══════════════════════════════════════════════════════════════════════════════
import asyncio as _asyncio
from fastapi import WebSocket as _WS, WebSocketDisconnect as _WSD
from fastapi.responses import StreamingResponse as _SR, Response as _Resp
from starlette.websockets import WebSocketState as _WSState

# Buffer: tetasco_id (str) -> bytes JPEG terbaru
_cam_frames: dict[str, bytes] = {}
_cam_ts:     dict[str, float] = {}      # timestamp frame terakhir
_cam_fps_c:  dict[str, int]   = {}      # frame counter
_cam_fps_v:  dict[str, float] = {}      # FPS value
_cam_fps_t:  dict[str, float] = {}      # FPS calc timestamp


@app.websocket("/api/tetasco/{tetasco_id}/camera/push")
async def camera_push(ws: _WS, tetasco_id: int):
    """
    Raspi connect ke sini via WebSocket dan kirim frame JPEG tiap ~50ms.
    Protocol: binary frame JPEG langsung (tanpa framing tambahan).
    """
    await ws.accept()
    key = str(tetasco_id)
    logger.info(f"[Camera] Raspi {tetasco_id} terhubung, mulai push frame")
    _cam_fps_c[key] = 0
    _cam_fps_t[key] = __import__("time").time()
    try:
        while True:
            data = await ws.receive_bytes()
            if data:
                _cam_frames[key] = data
                now = __import__("time").time()
                _cam_ts[key] = now
                _cam_fps_c[key] = _cam_fps_c.get(key, 0) + 1
                elapsed = now - _cam_fps_t.get(key, now)
                if elapsed >= 2.0:
                    _cam_fps_v[key] = _cam_fps_c[key] / elapsed
                    _cam_fps_c[key] = 0
                    _cam_fps_t[key] = now
    except (_WSD, Exception) as exc:
        logger.info(f"[Camera] Raspi {tetasco_id} disconnect: {exc}")


@app.get("/api/tetasco/{tetasco_id}/camera/stream")
async def camera_stream(tetasco_id: int):
    """
    MJPEG live stream. Buka di <img src=...> atau browser.
    URL: tetasco.my.id/api/tetasco/{id}/camera/stream
    """
    key = str(tetasco_id)

    async def _gen():
        prev = None
        while True:
            frame = _cam_frames.get(key)
            if frame and frame is not prev:
                prev = frame
                yield (
                    b"--frame\\r\\n"
                    b"Content-Type: image/jpeg\\r\\n\\r\\n"
                    + frame + b"\\r\\n"
                )
            await _asyncio.sleep(0.04)  # ~25 FPS max

    return _SR(
        _gen(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )


@app.get("/api/tetasco/{tetasco_id}/camera/snapshot")
async def camera_snapshot(tetasco_id: int):
    """Ambil 1 frame JPEG terbaru."""
    frame = _cam_frames.get(str(tetasco_id))
    if not frame:
        raise HTTPException(status_code=503, detail="Kamera tidak tersedia atau belum ada frame")
    return _Resp(frame, media_type="image/jpeg",
                 headers={"Cache-Control": "no-cache"})


@app.get("/api/tetasco/{tetasco_id}/camera/stats")
async def camera_stats(tetasco_id: int):
    """FPS dan status kamera live."""
    key = str(tetasco_id)
    ts  = _cam_ts.get(key)
    now = __import__("time").time()
    online = bool(ts and (now - ts) < 10)
    return {
        "tetascoId": tetasco_id,
        "online":    online,
        "fps":       round(_cam_fps_v.get(key, 0.0), 1),
        "lastFrame": ts,
        "streamUrl": f"/api/tetasco/{tetasco_id}/camera/stream",
    }

'''

# Sisipkan sebelum akhir file (tapi setelah semua route lain)
if '/api/tetasco/{tetasco_id}/camera/stream' in main_py:
    print('[INFO] Camera endpoints sudah ada di main.py')
else:
    main_py = main_py.rstrip() + '\n' + CAMERA_ENDPOINTS
    print('[OK] Camera endpoints ditambahkan ke main.py')

upload(sv, main_py, '/home/telur/tetasco-connect/backend/main.py')
print('[OK] main.py uploaded ke server')

# ─── 4. Patch Nginx config untuk MJPEG streaming ──────────────────────────────
i,o,e = sv.exec_command('cat ~/tetasco-connect/nginx/nginx.conf')
nginx_conf = o.read().decode('utf-8','replace')

CAMERA_NGINX = '''
        # ── Camera Streaming (MJPEG) — perlu buffering off ────────────────────
        location ~ ^/api/tetasco/[0-9]+/camera/ {
            set $backend_upstream "http://tetasco-backend:8000";
            proxy_pass         $backend_upstream;
            proxy_http_version 1.1;
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   Upgrade           $http_upgrade;
            proxy_set_header   Connection        $http_upgrade;
            proxy_buffering    off;
            proxy_cache        off;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            add_header         X-Accel-Buffering no;
        }
'''

if 'camera' not in nginx_conf:
    # Sisipkan sebelum blok location /api/
    nginx_conf = nginx_conf.replace(
        '        location /api/ {',
        CAMERA_NGINX + '\n        location /api/ {',
        1
    )
    upload(sv, nginx_conf, '/home/telur/tetasco-connect/nginx/nginx.conf')
    print('[OK] Nginx config updated (camera streaming block)')
else:
    print('[INFO] Camera block sudah ada di nginx.conf')

# ─── 5. Rebuild dan restart docker di server ──────────────────────────────────
r(sv, 'cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5',
  '5. Docker build backend', timeout=120)
r(sv, 'cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -8',
  '6. Docker up', timeout=60)
time.sleep(8)
r(sv, 'curl -s http://localhost:8000/api/health 2>/dev/null | head -1 || curl -s http://localhost:80/api/health 2>/dev/null | head -1 || echo "health check"',
  '7. Server health check')
r(sv, 'curl -s "http://localhost:8000/api/tetasco/1/camera/stats"',
  '8. Camera stats endpoint')

# ─── 6. Patch Raspi backend — WebSocket frame pusher ke server ────────────────
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')
print(f'\n[INFO] Raspi app.py: {len(app_py)} chars')

# Ambil tetascoId dari app.py
tid_match = re.search(r'TETASCO_ID\s*=\s*["\']?(\d+)', app_py)
tetasco_id = tid_match.group(1) if tid_match else '1'
print(f'[INFO] TETASCO_ID: {tetasco_id}')

WS_PUSHER_CODE = f'''

# ── Camera WebSocket Pusher — kirim frame ke tetasco.my.id ──────────────────
import websocket as _ws_client
import _thread

TETASCO_SERVER_WS = "ws://tetasco.my.id/api/tetasco/{tetasco_id}/camera/push"

def _camera_ws_push_thread():
    """Background: capture webcam + push frame via WebSocket ke server."""
    import time as _t, cv2 as _cv2
    while True:
        try:
            ws = _ws_client.create_connection(TETASCO_SERVER_WS, timeout=10)
            logger.info("[CamPush] Terhubung ke server, mulai push frame")
            cap = _cv2.VideoCapture("/dev/video0", _cv2.CAP_V4L2)
            cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(_cv2.CAP_PROP_FPS, 20)
            _t.sleep(1.0)
            while True:
                if not cap.grab():
                    _t.sleep(0.05); continue
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    continue
                ok, buf = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    ws.send_binary(buf.tobytes())
                _t.sleep(0.05)  # ~20 FPS
        except Exception as exc:
            logger.warning(f"[CamPush] Error: {{exc}}, reconnect 5 detik...")
            try: cap.release()
            except: pass
            _t.sleep(5)

# Mulai thread pusher (cek webcam tersedia dulu)
import os as _os
if _os.path.exists("/dev/video0"):
    try:
        import websocket  # noqa
        _thread.start_new_thread(_camera_ws_push_thread, ())
        logger.info("[CamPush] Thread dimulai → push ke " + TETASCO_SERVER_WS)
    except ImportError:
        logger.warning("[CamPush] websocket-client tidak terinstall, skip camera push")
else:
    logger.info("[CamPush] /dev/video0 tidak ada, skip camera push")

'''

if 'TETASCO_SERVER_WS' not in app_py:
    # Sisipkan sebelum if __name__
    if "if __name__ == '__main__':" in app_py:
        app_py = app_py.replace(
            "if __name__ == '__main__':",
            WS_PUSHER_CODE + "\nif __name__ == '__main__':",
            1
        )
    else:
        app_py += WS_PUSHER_CODE

    upload(rs, app_py, '/home/tetasco1/Penetas-Telur/backend/app.py')
    print('[OK] Raspi app.py updated dengan WS pusher')
    
    # Install websocket-client di Raspi
    r(rs, 'pip3 install websocket-client 2>/dev/null | tail -2', '9. Install websocket-client di Raspi', timeout=60)
else:
    print('[INFO] WS pusher sudah ada di Raspi')

# Restart Raspi backend
r(rs, 'pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '10. Kill Raspi backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(10)
r(rs, 'curl -s http://localhost:5001/api/health | python3 -c "import sys,json;print(json.load(sys.stdin)[\'status\'])"', '11. Raspi backend health')
r(rs, 'grep -i "CamPush\|camera\|error\|Error" /tmp/tetasco_backend.log | tail -8', '12. Raspi log')

sv.close()
rs.close()

print(f'''
✅ SELESAI! Camera relay aktif:

Stream URL (dari mana saja):
  https://tetasco.my.id/api/tetasco/{tetasco_id}/camera/stream
  https://tetasco.my.id/api/tetasco/{tetasco_id}/camera/snapshot
  https://tetasco.my.id/api/tetasco/{tetasco_id}/camera/stats
''')
