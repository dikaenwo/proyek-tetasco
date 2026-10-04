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

i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')
print(f'app.py: {len(app_py)} chars')

# Hapus seluruh blok camera lama dan ganti dengan versi simpel
import re

# Cari dan hapus blok camera lama (dari "# ── Camera Streaming" sampai sebelum "if __name__")
pattern = r'# ── Camera Streaming.*?(?=\nif __name__|$)'
old_camera = re.search(pattern, app_py, re.DOTALL)
if old_camera:
    print(f'[OK] Blok camera lama ditemukan, mengganti...')
    app_py = app_py[:old_camera.start()] + app_py[old_camera.end():]
else:
    print('[WARN] Blok camera lama tidak ditemukan, append ke akhir')

# Sisipkan sebelum "if __name__"
CAMERA_NEW = '''
# ── Camera Streaming (MJPEG — Direct Capture) ───────────────────────────────
import cv2 as _cv2

@app.route('/api/camera/stream')
def api_camera_stream():
    """Live MJPEG stream dari webcam USB (/dev/video0)."""
    def _gen():
        import time as _t
        cap = _cv2.VideoCapture(0)
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 15)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 1)
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    _t.sleep(0.05)
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
                if ok:
                    yield (b'--frame\\r\\n'
                           b'Content-Type: image/jpeg\\r\\n\\r\\n'
                           + buf.tobytes() + b'\\r\\n')
                _t.sleep(0.05)  # ~20 FPS
        finally:
            cap.release()

    return Response(_gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/snapshot')
def api_camera_snapshot():
    """Satu snapshot JPEG dari webcam."""
    import time as _t
    cap = _cv2.VideoCapture(0)
    cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
    _t.sleep(0.3)
    ret, frame = cap.read()
    cap.release()
    if ret:
        ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            return Response(buf.tobytes(), mimetype='image/jpeg',
                            headers={'Cache-Control': 'no-cache'})
    return jsonify({'error': 'Kamera tidak tersedia'}), 503

@app.route('/camera')
def page_camera():
    """Halaman viewer kamera."""
    return """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kamera Inkubator — Tetasco</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0D1117;color:#fff;font-family:system-ui,sans-serif;
     min-height:100vh;display:flex;flex-direction:column;align-items:center;
     padding:16px;gap:16px}
h1{font-size:1.1rem;color:#52C97F;margin-top:8px}
.wrap{width:100%;max-width:800px;border-radius:16px;overflow:hidden;
      border:2px solid rgba(82,201,127,.3);background:#111;aspect-ratio:4/3}
img{width:100%;height:100%;object-fit:cover;display:block}
.row{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
a,button{padding:10px 20px;background:#2F6B3F;border:none;border-radius:10px;
         color:#fff;font-size:.875rem;cursor:pointer;text-decoration:none;
         display:inline-block}
button{background:#1d3a28}
.info{font-size:.75rem;color:rgba(255,255,255,.4)}
</style>
</head>
<body>
<h1>🎥 Live Kamera Inkubator</h1>
<div class="wrap">
  <img id="stream" src="/api/camera/stream" alt="Live Stream">
</div>
<div class="row">
  <a href="/api/camera/snapshot" download="snapshot.jpg">📷 Simpan Foto</a>
  <button onclick="document.getElementById('stream').src='/api/camera/stream?t='+Date.now()">🔄 Refresh</button>
  <a href="/">← Dashboard</a>
</div>
<p class="info">MJPEG Stream · 20 FPS · 640×480 · /dev/video0</p>
</body>
</html>"""

'''

if "if __name__ == '__main__':" in app_py:
    app_py = app_py.replace(
        "if __name__ == '__main__':",
        CAMERA_NEW + "\nif __name__ == '__main__':",
        1
    )
else:
    app_py += CAMERA_NEW

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py uploaded — direct capture tanpa background thread')

# Restart backend
rs.exec_command('pkill -9 -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(\'OK\',d[\'status\'])"', 'Backend health')
r('grep -i "error\|Error\|camera\|Camera" /tmp/tetasco_backend.log | tail -5', 'Log')

# Test stream — pakai timeout lebih panjang (kamera init ~2 detik)
r('''python3 -c "
import socket, time
try:
    s = socket.create_connection((\'localhost\', 5001), timeout=5)
    req = b\'GET /api/camera/stream HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n\'
    s.send(req)
    data = b\'\'
    s.settimeout(10)
    start = time.time()
    while time.time()-start < 10:
        try:
            chunk = s.recv(4096)
            if not chunk: break
            data += chunk
            if len(data) > 8000: break
        except socket.timeout: break
    s.close()
    if b\'image/jpeg\' in data:
        print(f\'STREAM OK! {len(data)} bytes, JPEG frame diterima \u2705\')
    elif b\'500\' in data[:200]:
        print(\'Error 500:\', data[:500].decode(errors=\'replace\'))
    else:
        print(\'Data:\', data[:400].decode(errors=\'replace\'))
except Exception as e:
    print(\'Error:\', e)
"''', 'Test stream via raw socket (10 detik)', timeout=25)

rs.close()
print('\n✅ Buka di browser PC: http://192.168.1.27:5001/camera')
