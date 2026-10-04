"""add_camera_stream.py — Tambah endpoint MJPEG streaming ke Flask backend Raspi"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# 1. Baca app.py
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')
print(f'[INFO] app.py: {len(app_py)} chars')

# 2. Cek apakah sudah ada camera endpoint
if '/api/camera/stream' in app_py:
    print('[INFO] Camera endpoint sudah ada!')
else:
    # Tambahkan import cv2 dan endpoint streaming setelah baris import terakhir
    CAMERA_CODE = '''

# ── Camera Streaming (MJPEG) ────────────────────────────────────────────────
import cv2 as _cv2
import threading as _threading

_cam_lock  = _threading.Lock()
_cam_frame = None   # Latest JPEG bytes
_cam_thread_started = False

def _camera_capture_thread(device=0):
    """Background thread: terus capture frame dari webcam."""
    global _cam_frame
    cap = _cv2.VideoCapture(device)
    cap.set(_cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(_cv2.CAP_PROP_FPS, 15)
    logger.info(f'[Camera] Streaming dari /dev/video{device}')
    while True:
        ret, frame = cap.read()
        if not ret:
            _cv2.waitKey(100)
            continue
        ret2, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
        if ret2:
            with _cam_lock:
                _cam_frame = buf.tobytes()

def _start_camera(device=0):
    global _cam_thread_started
    if not _cam_thread_started:
        t = _threading.Thread(target=_camera_capture_thread, args=(device,), daemon=True)
        t.start()
        _cam_thread_started = True

def _generate_mjpeg():
    """Generator: kirim frame satu per satu sebagai MJPEG."""
    import time as _time
    _start_camera(0)
    while True:
        with _cam_lock:
            frame = _cam_frame
        if frame:
            yield (
                b'--frame\\r\\n'
                b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame + b'\\r\\n'
            )
        _time.sleep(1 / 15)  # ~15 FPS

@app.route('/api/camera/stream')
def api_camera_stream():
    """MJPEG stream dari webcam. Buka di browser atau <img src=...>"""
    return Response(
        _generate_mjpeg(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/camera/snapshot')
def api_camera_snapshot():
    """Ambil satu frame JPEG dari webcam."""
    _start_camera(0)
    _time_mod = __import__('time')
    _time_mod.sleep(0.5)
    with _cam_lock:
        frame = _cam_frame
    if frame:
        return Response(frame, mimetype='image/jpeg',
                        headers={'Cache-Control': 'no-cache'})
    return jsonify({'error': 'Kamera tidak tersedia'}), 503

@app.route('/camera')
def page_camera():
    """Halaman viewer webcam sederhana."""
    return """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kamera Inkubator — Tetasco</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#0D1117; color:#FFF; font-family:sans-serif; min-height:100vh;
         display:flex; flex-direction:column; align-items:center; padding:20px; }
  h1 { font-size:1.25rem; margin-bottom:16px; color:#52C97F; }
  .stream-wrap { width:100%; max-width:800px; border-radius:16px; overflow:hidden;
                 border:2px solid rgba(82,201,127,0.3); background:#111; }
  img { width:100%; display:block; }
  .info { margin-top:12px; font-size:0.8rem; color:rgba(255,255,255,0.4); }
  .btn { margin-top:16px; padding:10px 24px; background:#2F6B3F; border:none;
         border-radius:10px; color:#FFF; font-size:0.9rem; cursor:pointer;
         text-decoration:none; display:inline-block; }
</style>
</head>
<body>
<h1>🎥 Live Kamera Inkubator</h1>
<div class="stream-wrap">
  <img src="/api/camera/stream" alt="Live Stream" id="stream">
</div>
<p class="info">Stream langsung dari webcam · 15 FPS · MJPEG</p>
<a href="/" class="btn">← Kembali ke Dashboard</a>
</body>
</html>"""

'''

    # Sisipkan sebelum baris `if __name__ == '__main__':` atau sebelum akhir file
    if "if __name__ == '__main__':" in app_py:
        app_py = app_py.replace(
            "if __name__ == '__main__':",
            CAMERA_CODE + "\nif __name__ == '__main__':",
            1
        )
    else:
        app_py += CAMERA_CODE

    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] Camera endpoints ditambahkan ke app.py')

# 3. Restart backend
r('pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '3. Kill backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)
r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(\'Backend:\',d[\'status\'],\'|\',d[\'version\'])"',
  '4. Backend health')
r('tail -5 /tmp/tetasco_backend.log', '5. Backend log')

# 4. Test endpoint kamera
r('curl -s --max-time 3 -I http://localhost:5001/api/camera/stream 2>/dev/null | head -5', '6. Camera stream header')

# 5. Cek apakah video0 bisa dibuka oleh user tetasco1
r('python3 -c "import cv2; cap=cv2.VideoCapture(0); print(\'Kamera OK:\', cap.isOpened()); cap.release()"',
  '7. Test cv2.VideoCapture(0)')

rs.close()

ip = '192.168.1.27'
print(f'\n✅ SELESAI!')
print(f'   Buka di browser PC: http://{ip}:5001/camera')
print(f'   Stream langsung:    http://{ip}:5001/api/camera/stream')
