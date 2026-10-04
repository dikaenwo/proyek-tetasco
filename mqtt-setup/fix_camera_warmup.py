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

OLD_GEN = '''def _generate_mjpeg():
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
        _time.sleep(1 / 15)  # ~15 FPS'''

NEW_GEN = '''def _generate_mjpeg():
    """Generator: kirim frame satu per satu sebagai MJPEG."""
    import time as _time
    _start_camera(0)
    # Tunggu frame pertama (camera warmup ~1-2 detik)
    for _ in range(40):
        with _cam_lock:
            if _cam_frame is not None:
                break
        _time.sleep(0.1)
    prev = None
    while True:
        with _cam_lock:
            frame = _cam_frame
        if frame and frame is not prev:
            prev = frame
            yield (
                b'--frame\\r\\n'
                b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame + b'\\r\\n'
            )
        _time.sleep(1 / 20)  # ~20 FPS'''

if OLD_GEN in app_py:
    app_py = app_py.replace(OLD_GEN, NEW_GEN, 1)
    print('[OK] Generator dipatch — ada warmup wait')
else:
    print('[WARN] Pattern tidak ditemukan, patch manual')
    # Cari dan tampilkan
    idx = app_py.find('def _generate_mjpeg')
    if idx > -1:
        print(app_py[idx:idx+400])

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()

# Restart
rs.exec_command('pkill -9 -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(\'OK\',d[\'status\'])"', 'Backend health')

# Test stream dengan timeout lebih panjang
r('''python3 -c "
import urllib.request, time
try:
    req = urllib.request.urlopen(\'http://localhost:5001/api/camera/stream\', timeout=10)
    print(\'Connection OK, membaca frame...\')
    data = b\'\'
    start = time.time()
    while len(data) < 5000 and time.time()-start < 8:
        chunk = req.read(512)
        if not chunk: break
        data += chunk
    req.close()
    if b\'--frame\' in data:
        print(f\'STREAM OK! {len(data)} bytes diterima ✅\')
    else:
        print(\'Data:\', data[:300])
except Exception as e:
    print(\'Error:\', e)
"''', 'Test stream (8 detik timeout)')

rs.close()
print('\n✅ Coba buka: http://192.168.1.27:5001/camera')
