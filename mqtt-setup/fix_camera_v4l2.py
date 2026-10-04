"""fix_camera_v4l2.py — Patch camera endpoint pakai V4L2 backend + grab/retrieve"""
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

# === Test cv2 dalam thread dulu ===
TEST_SCRIPT = """
import cv2, threading, time
result = {}
def capture():
    cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(1.0)
    ret, frame = cap.read()
    result['ret'] = ret
    result['shape'] = frame.shape if ret else None
    cap.release()

t = threading.Thread(target=capture)
t.start()
t.join(timeout=8)
print('Thread ret:', result.get('ret'), 'shape:', result.get('shape'))
"""
sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(TEST_SCRIPT.encode()), '/tmp/test_cam.py')
sftp.close()
r('python3 /tmp/test_cam.py', '1. Test cv2 dalam thread + V4L2', timeout=15)

# === Baca dan patch app.py ===
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')
print(f'\n[INFO] app.py: {len(app_py)} chars')

OLD_GEN = '''    def _gen():
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
            cap.release()'''

NEW_GEN = '''    def _gen():
        import time as _t
        # V4L2 backend eksplisit agar work di threading context
        cap = _cv2.VideoCapture('/dev/video0', _cv2.CAP_V4L2)
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 20)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 2)
        _t.sleep(1.2)  # Warmup kamera
        try:
            while True:
                # grab() = ambil frame; retrieve() = decode
                if not cap.grab():
                    _t.sleep(0.05)
                    continue
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
                if ok:
                    yield (b'--frame\\r\\n'
                           b'Content-Type: image/jpeg\\r\\n\\r\\n'
                           + buf.tobytes() + b'\\r\\n')
                _t.sleep(0.05)  # ~20 FPS
        finally:
            cap.release()'''

if OLD_GEN in app_py:
    app_py = app_py.replace(OLD_GEN, NEW_GEN, 1)
    sftp2 = rs.open_sftp()
    sftp2.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp2.close()
    print('[OK] Patch V4L2 + grab/retrieve berhasil')
else:
    print('[WARN] Pattern tidak ditemukan! Cari context:')
    idx = app_py.find('VideoCapture(0)')
    print(app_py[max(0,idx-50):idx+200] if idx>-1 else 'Not found')

# Restart
r('pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', '2. Kill backend')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(d[\'status\'])"', '3. Backend health')
r('grep -i "error\|Error\|camera" /tmp/tetasco_backend.log | tail -5', '4. Log')

# Test stream 10 detik
r('timeout 10 curl -s http://localhost:5001/api/camera/stream | wc -c || echo "timeout"', '5. Stream bytes (10 detik)', timeout=15)

rs.close()
print('\n✅ Buka: http://192.168.1.27:5001/camera')
