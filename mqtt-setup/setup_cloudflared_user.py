"""setup_cloudflared_user.py — Install cloudflared ke ~/.local/bin/ (no sudo) + setup /api/camera/stats + /api/tunnel-url"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=60):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# 1. Install cloudflared ke ~/.local/bin/
r('mkdir -p ~/.local/bin', '1. Create ~/.local/bin')
r('curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64" -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared && echo "OK"',
  '2. Download cloudflared', timeout=120)
r('~/.local/bin/cloudflared --version', '3. Versi')

# 2. Jalankan quick tunnel
print('\n[4. Start quick tunnel...]', flush=True)
rs.exec_command('pkill -f cloudflared 2>/dev/null || true')
time.sleep(2)
rs.exec_command('nohup ~/.local/bin/cloudflared tunnel --url http://localhost:5001 > /tmp/cloudflared.log 2>&1 &')
time.sleep(15)  # Tunggu tunnel establish

log = r('cat /tmp/cloudflared.log', '5. Tunnel log (15 detik)')

import re
urls = re.findall(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', log)
tunnel_url = urls[0] if urls else None
if tunnel_url:
    print(f'\n✅ TUNNEL URL: {tunnel_url}')
else:
    print('[WARN] URL belum muncul, tunggu lebih lama...')

# 3. Tambah endpoint /api/camera/stats dan /api/tunnel-url ke app.py
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')
print(f'\n[INFO] app.py: {len(app_py)} chars')

# Cek apakah sudah ada
if '/api/camera/stats' in app_py:
    print('[INFO] /api/camera/stats sudah ada')
else:
    STATS_CODE = '''
# ── Camera Stats + Tunnel URL ────────────────────────────────────────────────
import time as _time_mod

_cam_frame_count = 0
_cam_fps         = 0.0
_cam_fps_ts      = _time_mod.time()
_cam_width       = 640
_cam_height      = 480
_tunnel_url      = None  # Diisi oleh cloudflared watcher

def _update_fps():
    global _cam_fps, _cam_fps_ts, _cam_frame_count
    now = _time_mod.time()
    elapsed = now - _cam_fps_ts
    if elapsed >= 2.0:
        _cam_fps    = _cam_frame_count / elapsed
        _cam_frame_count = 0
        _cam_fps_ts = now

def _watch_tunnel_log():
    """Background thread: baca /tmp/cloudflared.log dan update _tunnel_url."""
    import re as _re
    global _tunnel_url
    while True:
        try:
            with open('/tmp/cloudflared.log', 'r', errors='replace') as f:
                content = f.read()
            urls = _re.findall(r'https://[a-zA-Z0-9\\-]+\\.trycloudflare\\.com', content)
            if urls:
                _tunnel_url = urls[0]
        except Exception:
            pass
        _time_mod.sleep(10)

_threading_mod = __import__('threading')
_tw = _threading_mod.Thread(target=_watch_tunnel_log, daemon=True)
_tw.start()

@app.route('/api/camera/stats')
def api_camera_stats():
    """FPS, resolusi kamera, dan tunnel URL."""
    _update_fps()
    return jsonify({
        'fps':    round(_cam_fps, 1),
        'width':  _cam_width,
        'height': _cam_height,
        'tunnel': _tunnel_url,
    })

@app.route('/api/tunnel-url')
def api_tunnel_url():
    """Kembalikan public tunnel URL jika tersedia."""
    if _tunnel_url:
        return jsonify({'url': _tunnel_url, 'available': True})
    return jsonify({'url': None, 'available': False})

'''
    # Tambah sebelum if __name__
    if "if __name__ == '__main__':" in app_py:
        app_py = app_py.replace(
            "if __name__ == '__main__':",
            STATS_CODE + "\nif __name__ == '__main__':",
            1
        )

# 4. Patch _generate_mjpeg untuk update frame count
OLD_ENCODE = '''                if ok:
                    yield (b'--frame\\r\\n'
                           b'Content-Type: image/jpeg\\r\\n\\r\\n'
                           + buf.tobytes() + b'\\r\\n')
                _t.sleep(0.05)  # ~20 FPS'''

NEW_ENCODE = '''                if ok:
                    global _cam_frame_count, _cam_width, _cam_height
                    _cam_frame_count += 1
                    _cam_width  = frame.shape[1]
                    _cam_height = frame.shape[0]
                    yield (b'--frame\\r\\n'
                           b'Content-Type: image/jpeg\\r\\n\\r\\n'
                           + buf.tobytes() + b'\\r\\n')
                _t.sleep(0.05)  # ~20 FPS'''

if OLD_ENCODE in app_py:
    app_py = app_py.replace(OLD_ENCODE, NEW_ENCODE, 1)
    print('[OK] Frame counter ditambah ke generator')

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py updated')

# 5. Restart backend
rs.exec_command('pkill -9 -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(8)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;print(json.load(sys.stdin)[\'status\'])"', '6. Backend health')
r('curl -s http://localhost:5001/api/camera/stats', '7. Camera stats')
r('curl -s http://localhost:5001/api/tunnel-url', '8. Tunnel URL')

rs.close()

if tunnel_url:
    print(f'\n✅ Akses dari luar jaringan:')
    print(f'   Stream:  {tunnel_url}/api/camera/stream')
    print(f'   Viewer:  {tunnel_url}/camera')
    print(f'   Stats:   {tunnel_url}/api/camera/stats')
else:
    print('\n[INFO] Tunggu ~30 detik lagi, cek /api/tunnel-url dari HP')
