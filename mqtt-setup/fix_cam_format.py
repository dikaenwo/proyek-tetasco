import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

OLD_CAP = '''        cap = _cv2.VideoCapture(dev, backend)
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 20)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():'''

NEW_CAP = '''        cap = _cv2.VideoCapture(dev, backend)
        # JETE-W7 default = MJPG → OpenCV sering decode salah → gambar corrupted
        # Fix: paksa YUYV (raw) agar OpenCV decode & encode ulang ke JPEG dengan benar
        cap.set(_cv2.CAP_PROP_FOURCC, _cv2.VideoWriter_fourcc(*'YUYV'))
        cap.set(_cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(_cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(_cv2.CAP_PROP_FPS, 30)
        cap.set(_cv2.CAP_PROP_BUFFERSIZE, 1)  # buffer minimum → frame paling fresh

        if not cap.isOpened():'''

OLD_CAPTURE = '''                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(f"[CameraHub] Frame gagal dibaca dari {dev}, coba ulang...")
                    time.sleep(0.1)
                    continue

                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])'''

NEW_CAPTURE = '''                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(f"[CameraHub] Frame gagal dibaca dari {dev}, coba ulang...")
                    time.sleep(0.1)
                    continue

                # Pastikan frame valid (tidak kosong, dimensi benar)
                if frame.shape[0] < 10 or frame.shape[1] < 10:
                    continue

                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])'''

changed = 0
if OLD_CAP in app:
    app = app.replace(OLD_CAP, NEW_CAP, 1)
    print('[OK] FOURCC YUYV + FPS 30 ditambah')
    changed += 1
else:
    print('[WARN] CAP block tidak cocok')

if OLD_CAPTURE in app:
    app = app.replace(OLD_CAPTURE, NEW_CAPTURE, 1)
    print('[OK] Frame validation + quality 85')
    changed += 1
else:
    print('[WARN] imencode block tidak cocok')
    # Fallback: cari dan tambah FOURCC saja via regex
    import re
    m = re.search(r'(cap\.set\(_cv2\.CAP_PROP_FRAME_WIDTH)', app)
    if m:
        insert_pos = app.rfind('\n', 0, m.start()) + 1
        fourcc_line = "        cap.set(_cv2.CAP_PROP_FOURCC, _cv2.VideoWriter_fourcc(*'YUYV'))\n"
        if 'FOURCC' not in app:
            app = app[:insert_pos] + fourcc_line + app[insert_pos:]
            print('[OK] FOURCC inserted via regex fallback')

if changed == 0:
    print('[ERR] Tidak ada yang berubah')
else:
    sftp = rp.open_sftp()
    sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()

    i2,o2,e2 = rp.exec_command('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK')
    print('[Syntax]', o2.read().decode().strip())

    # Restart
    rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
    time.sleep(2)
    chan = rp.get_transport().open_session()
    chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
    time.sleep(1); chan.close()
    print('[OK] Restart')
    time.sleep(10)

    i3,o3,e3 = rp.exec_command('grep -i "YUYV\\|FOURCC\\|camera\\|video0\\|berhasil" /tmp/tetasco_backend.log | tail -5')
    print(o3.read().decode().strip())

rp.close()
print('\n✅ Refresh https://tetasco.my.id/api/tetasco/1/camera/snapshot')
