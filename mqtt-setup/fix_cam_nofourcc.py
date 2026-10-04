import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Cek FOURCC saat ini
OLD_FOURCC = """        cap = _cv2.VideoCapture(dev, backend)
        # JETE-W7 default = MJPG → OpenCV sering decode salah → gambar corrupted
        # Fix: paksa YUYV (raw) agar OpenCV decode & encode ulang ke JPEG dengan benar
        cap.set(_cv2.CAP_PROP_FOURCC, _cv2.VideoWriter_fourcc(*'YUYV'))
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 30)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 1)  # buffer minimum → frame paling fresh"""

NEW_FOURCC = """        cap = _cv2.VideoCapture(dev, backend)
        # Biarkan V4L2 pilih format native (biasanya MJPG).
        # Jangan override FOURCC — mismatch MJPG↔YUYV → frame corrupted.
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 30)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 2)   # buffer 2 agar tidak starvation
        cap.set(_cv2.CAP_PROP_CONVERT_RGB, 1)  # pastikan output BGR untuk imencode"""

if OLD_FOURCC in app:
    app = app.replace(OLD_FOURCC, NEW_FOURCC, 1)
    print('[OK] FOURCC override dihapus, CONVERT_RGB=1 ditambah')
else:
    print('[WARN] Pattern tidak cocok, patch manual...')
    import re
    # Hapus baris FOURCC saja
    app = re.sub(
        r"        cap\.set\(_cv2\.CAP_PROP_FOURCC.*?\n",
        "",
        app
    )
    # Tambah CONVERT_RGB setelah BUFFERSIZE
    app = app.replace(
        "cap.set(_cv2.CAP_PROP_BUFFERSIZE, 1)",
        "cap.set(_cv2.CAP_PROP_BUFFERSIZE, 2)\n        cap.set(_cv2.CAP_PROP_CONVERT_RGB, 1)"
    )
    print('[OK] Patched manual')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()

i2,o2,e2 = rp.exec_command('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK')
print(o2.read().decode().strip())

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart, tunggu warmup...')
time.sleep(15)

i3,o3,e3 = rp.exec_command('grep -i "warmup\|berhasil\|CamPush\|terhubung" /tmp/tetasco_backend.log | tail -5')
print(o3.read().decode().strip())
rp.close()
print('\n✅ Refresh snapshot dan cek!')
