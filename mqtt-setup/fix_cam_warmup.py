import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Patch 1: tambah warmup setelah kamera berhasil dibuka
OLD_OPEN = '''        logger.info(f"[CameraHub] ✅ Kamera {dev} BERHASIL dibuka & aktif!")
        _camera_active = True

        try:
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.04)
                    continue

                # Validasi frame sebelum encode
                if frame is None or frame.size == 0 or frame.shape[0] < 10:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])'''

NEW_OPEN = '''        logger.info(f"[CameraHub] ✅ Kamera {dev} BERHASIL dibuka & aktif!")
        _camera_active = True

        # Warmup: buang frame pertama (sering corrupted saat USB handshake)
        logger.info("[CameraHub] Warmup — membuang 8 frame awal...")
        for _w in range(8):
            cap.grab()
            time.sleep(0.04)

        try:
            while not stop_event.is_set():
                # Double-grab: flush satu frame stale dulu, baru retrieve yang segar
                cap.grab()
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    time.sleep(0.04)
                    continue

                # Validasi dimensi frame
                if frame.size == 0 or frame.shape[0] < 10 or frame.shape[1] < 10:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 80])'''

if OLD_OPEN in app:
    app = app.replace(OLD_OPEN, NEW_OPEN, 1)
    print('[OK] Warmup + double-grab ditambah')
else:
    print('[WARN] Pattern tidak cocok, coba partial match...')
    # Cari dan ganti hanya bagian loop
    OLD2 = '''            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.04)
                    continue

                # Validasi frame sebelum encode
                if frame is None or frame.size == 0 or frame.shape[0] < 10:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])'''
    NEW2 = '''            while not stop_event.is_set():
                # Double-grab: flush stale frame, retrieve yang segar
                cap.grab()
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    time.sleep(0.04)
                    continue

                if frame.size == 0 or frame.shape[0] < 10 or frame.shape[1] < 10:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 80])'''
    if OLD2 in app:
        app = app.replace(OLD2, NEW2, 1)
        print('[OK] Loop patched (partial match)')
    else:
        print('[ERR] Tidak bisa patch')

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
print('[OK] Restart — tunggu ~15 detik untuk warmup kamera...')
time.sleep(15)

i3,o3,e3 = rp.exec_command('grep -i "warmup\|berhasil\|camera\|CamPush\|terhubung" /tmp/tetasco_backend.log | tail -8')
print(o3.read().decode().strip())

rp.close()
print('\n✅ Coba refresh snapshot sekarang!')
