import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Fix kualitas JPEG dan tambah frame validation
OLD = "                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])"
NEW = """                # Validasi frame sebelum encode
                if frame is None or frame.size == 0 or frame.shape[0] < 10:
                    continue
                ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 85])"""

if OLD in app:
    app = app.replace(OLD, NEW, 1)
    print('[OK] Frame validation + quality 85')
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
    print('[OK] Restart')
else:
    print('[WARN] Pattern tidak cocok, baris 639 tetap quality 75 (masih ok)')

rp.close()
