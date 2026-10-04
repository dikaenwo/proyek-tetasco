import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Hapus ping_interval dan ping_timeout — keduanya menyebabkan race condition
# karena websocket-client tidak thread-safe untuk concurrent send
OLD_CONN = '''            ws = _ws_client.create_connection(
                url, timeout=8,
                ping_interval=PING_INTERVAL,  # kirim ping tiap 15 detik → cegah timeout
                ping_timeout=5,
            )'''

NEW_CONN = '''            ws = _ws_client.create_connection(url, timeout=8)
            # JANGAN pakai ping_interval — websocket-client tidak thread-safe,
            # ping thread + frame send thread → race condition → broken pipe'''

if OLD_CONN in app:
    app = app.replace(OLD_CONN, NEW_CONN, 1)
    print('[OK] Hapus ping_interval/ping_timeout (race condition)')
else:
    print('[WARN] create_connection pattern tidak cocok')

# Hapus konstanta PING_INTERVAL yang tidak terpakai
OLD_PING_VAR = '''    PING_INTERVAL = 15  # detik antar ping keepalive

    while not stop_event.is_set():'''
NEW_PING_VAR = '''    while not stop_event.is_set():'''

if OLD_PING_VAR in app:
    app = app.replace(OLD_PING_VAR, NEW_PING_VAR, 1)
    print('[OK] Hapus konstanta PING_INTERVAL')

# Juga pastikan inner loop selalu kirim frame (jangan idle)
# Kalau frame None → skip tapi tetap sleep pendek (jangan beri celah timeout)
OLD_SEND = '''            while not stop_event.is_set():
                with _latest_frame_lock:
                    frame_bytes = _latest_jpeg_frame
                if frame_bytes is not None:
                    ws.send_binary(frame_bytes)
                time.sleep(0.05) # ~20 FPS push'''

NEW_SEND = '''            while not stop_event.is_set():
                with _latest_frame_lock:
                    frame_bytes = _latest_jpeg_frame
                if frame_bytes is not None:
                    ws.send_binary(frame_bytes)
                    time.sleep(0.05)  # ~20 FPS
                else:
                    time.sleep(0.05)  # tunggu frame ready'''

if OLD_SEND in app:
    app = app.replace(OLD_SEND, NEW_SEND, 1)
    print('[OK] Inner loop dipastikan tidak idle')
else:
    print('[INFO] Inner loop pattern tidak cocok (mungkin sudah ok)')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()

i2,o2,e2 = rp.exec_command('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK')
print(o2.read().decode().strip())

rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(12)

i3,o3,e3 = rp.exec_command('grep -i "CamPush\|terhubung\|broken\|reconnect" /tmp/tetasco_backend.log | tail -6')
print(o3.read().decode().strip())
rp.close()
print('\n✅ Monitor: broken pipe harusnya hilang sekarang')
