import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Cari dan ganti seluruh fungsi _camera_ws_push_thread
OLD_PUSH = '''def _camera_ws_push_thread():
    """Background: push frame ke server — coba LAN dulu, fallback ke Cloudflare."""
    url_idx = 0  # mulai dari LAN
    while not stop_event.is_set():
        url = _CAM_PUSH_URLS[url_idx % len(_CAM_PUSH_URLS)]
        try:
            logger.info(f"[CamPush] Mencoba koneksi ke: {url}")
            ws = _ws_client.create_connection(url, timeout=5)
            logger.info(f"[CamPush] ✅ Terhubung via: {url}")
            url_idx = 0  # reset ke LAN setelah sukses'''

NEW_PUSH = '''def _camera_ws_push_thread():
    """Background: push JPEG frame ke server via WebSocket dengan auto-reconnect."""
    url_idx   = 0   # mulai dari LAN
    fail_count = 0  # gagal berturut-turut — baru ganti URL setelah 3 kali
    PING_INTERVAL = 15  # detik antar ping keepalive

    while not stop_event.is_set():
        url = _CAM_PUSH_URLS[url_idx % len(_CAM_PUSH_URLS)]
        try:
            logger.info(f"[CamPush] Mencoba koneksi ke: {url}")
            ws = _ws_client.create_connection(
                url, timeout=8,
                ping_interval=PING_INTERVAL,  # kirim ping tiap 15 detik → cegah timeout
                ping_timeout=5,
            )
            logger.info(f"[CamPush] ✅ Terhubung via: {url}")
            fail_count = 0
            url_idx = 0  # reset ke LAN setelah sukses'''

if OLD_PUSH in app:
    app = app.replace(OLD_PUSH, NEW_PUSH, 1)
    print('[OK] Patch 1: ping_interval=15 + fail_count logic')
else:
    print('[WARN] Push thread header tidak cocok')

# Patch 2: error handler — ganti URL hanya setelah gagal 3x berturut-turut
OLD_ERR = '''        except Exception as exc:
            logger.warning(f"[CamPush] Error {url}: {exc}")
            url_idx += 1  # coba URL berikutnya (LAN→Cloud atau Cloud→LAN)
            wait = 3 if url_idx % len(_CAM_PUSH_URLS) != 0 else 5
            logger.info(f"[CamPush] Fallback ke URL ke-{url_idx % len(_CAM_PUSH_URLS) + 1}, tunggu {wait}s...")
            time.sleep(wait)'''

NEW_ERR = '''        except Exception as exc:
            fail_count += 1
            is_broken_pipe = 'Broken pipe' in str(exc) or 'reset' in str(exc).lower()
            if is_broken_pipe:
                # Broken pipe = koneksi putus tiba-tiba — reconnect ke URL yang sama
                logger.warning(f"[CamPush] Koneksi putus (broken pipe), reconnect 2 detik...")
                time.sleep(2)
            elif fail_count >= 3:
                # Gagal 3x berturut → coba URL berikutnya
                url_idx += 1
                fail_count = 0
                logger.warning(f"[CamPush] Gagal 3x, beralih ke URL ke-{url_idx % len(_CAM_PUSH_URLS) + 1}")
                time.sleep(3)
            else:
                logger.warning(f"[CamPush] Error ({fail_count}/3): {exc}, retry 3 detik...")
                time.sleep(3)'''

if OLD_ERR in app:
    app = app.replace(OLD_ERR, NEW_ERR, 1)
    print('[OK] Patch 2: broken pipe reconnect cepat ke URL sama')
else:
    print('[WARN] Error handler tidak cocok')

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

i3,o3,e3 = rp.exec_command('grep -i "CamPush\|CameraHub\|terhubung\|warmup\|broken" /tmp/tetasco_backend.log | tail -8')
print(o3.read().decode().strip())
rp.close()
