import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o.read().decode('utf-8','replace')

# Ganti fungsi camera push dengan versi auto-fallback
OLD_CAM_PUSH = '''# ── Camera WebSocket Pusher — kirim frame ke tetasco.my.id ──────────────────
import websocket as _ws_client

# LAN IP (bypass Cloudflare) — lebih cepat dan stabil untuk push dalam jaringan lokal
TETASCO_SERVER_WS = "ws://192.168.1.14/api/tetasco/1/camera/push"

def _camera_ws_push_thread():
    """Background: push frame dari shared memory buffer ke WebSocket server cloud."""
    while not stop_event.is_set():
        try:
            ws = _ws_client.create_connection(TETASCO_SERVER_WS, timeout=10)
            logger.info("[CamPush] Terhubung ke server cloud WebSocket, mulai push frame")'''

NEW_CAM_PUSH = '''# ── Camera WebSocket Pusher — kirim frame ke tetasco.my.id ──────────────────
import websocket as _ws_client

# Auto-fallback: coba LAN dulu (cepat), fallback ke Cloudflare jika gagal
_CAM_PUSH_URLS = [
    "ws://192.168.1.14/api/tetasco/1/camera/push",       # LAN (prioritas)
    "wss://tetasco.my.id/api/tetasco/1/camera/push",     # Cloudflare (fallback)
]

def _camera_ws_push_thread():
    """Background: push frame ke server — coba LAN dulu, fallback ke Cloudflare."""
    url_idx = 0  # mulai dari LAN
    while not stop_event.is_set():
        url = _CAM_PUSH_URLS[url_idx % len(_CAM_PUSH_URLS)]
        try:
            logger.info(f"[CamPush] Mencoba koneksi ke: {url}")
            ws = _ws_client.create_connection(url, timeout=5)
            logger.info(f"[CamPush] ✅ Terhubung via: {url}")
            url_idx = 0  # reset ke LAN setelah sukses'''

if OLD_CAM_PUSH in app:
    app = app.replace(OLD_CAM_PUSH, NEW_CAM_PUSH, 1)
    print('[OK] Patch 1: camera push URLs dan koneksi awal')
else:
    print('[WARN] Pattern 1 tidak cocok')
    import re
    m = re.search(r'# ── Camera WebSocket Pusher.*?def _camera_ws_push_thread', app, re.DOTALL)
    if m: print('[DEBUG]', m.group()[:300])

# Patch 2: bagian except (error handling + fallback ke URL berikutnya)
OLD_EXCEPT = '''        except Exception as exc:
            logger.warning(f"[CamPush] Error: {exc}, reconnect 5 detik...")
            time.sleep(5)'''

NEW_EXCEPT = '''        except Exception as exc:
            logger.warning(f"[CamPush] Error {url}: {exc}")
            url_idx += 1  # coba URL berikutnya (LAN→Cloud atau Cloud→LAN)
            wait = 3 if url_idx % len(_CAM_PUSH_URLS) != 0 else 5
            logger.info(f"[CamPush] Fallback ke URL ke-{url_idx % len(_CAM_PUSH_URLS) + 1}, tunggu {wait}s...")
            time.sleep(wait)'''

if OLD_EXCEPT in app:
    app = app.replace(OLD_EXCEPT, NEW_EXCEPT, 1)
    print('[OK] Patch 2: error handling dengan fallback URL')
else:
    print('[WARN] Pattern 2 tidak cocok')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK', 'Syntax check')

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(10)

ras('grep -i "CamPush\|mencoba\|terhubung\|error\|fallback" /tmp/tetasco_backend.log | tail -10', 'Camera push log')
rp.close()
print('\n✅ Auto-fallback: LAN → Cloudflare')
