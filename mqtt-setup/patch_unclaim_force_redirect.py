"""patch_unclaim_force_redirect.py — Saat unclaim terdeteksi, Chromium dipaksa buka /pair"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

i, o, e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
content = o.read().decode('utf-8','replace')
print(f'[INFO] app.py: {len(content)} chars', flush=True)

# Ganti fungsi watcher agar juga restart Chromium ke /pair
OLD_WATCHER = '''def _unclaim_watcher_thread():
    """Cek setiap 60 detik apakah lemari di-unclaim dari server."""
    import time as _t, urllib.request as _ur, json as _j, ssl as _ssl
    while True:
        _t.sleep(60)
        try:
            if not _CLAIMED_FILE.exists():
                continue  # Belum claimed, tidak perlu cek
            tid = int(os.getenv('TETASCO_ID', 1))
            ctx = _ssl.create_default_context()
            req = _ur.Request(
                f'https://tetasco.my.id/api/tetasco/{tid}/is-claimed',
                headers={'User-Agent': 'TetascoRaspi/1.0', 'Accept': 'application/json'}
            )
            with _ur.urlopen(req, context=ctx, timeout=8) as resp:
                d = _j.loads(resp.read().decode())
                if not d.get('claimed'):
                    logger.info('[Unclaim Watcher] Lemari di-unclaim dari HP! Menghapus flag...')
                    _CLAIMED_FILE.unlink(missing_ok=True)
                    logger.info('[Unclaim Watcher] Flag dihapus. Browser akan redirect ke /pair otomatis.')
        except Exception as ex:
            logger.debug(f'[Unclaim Watcher] Error: {ex}')'''

NEW_WATCHER = '''def _unclaim_watcher_thread():
    """Cek setiap 30 detik apakah lemari di-unclaim dari server.
    Jika ya: hapus flag lokal LALU paksa Chromium buka halaman /pair.
    """
    import time as _t, urllib.request as _ur, json as _j, ssl as _ssl, subprocess as _sp
    while True:
        _t.sleep(30)
        try:
            # Cek via polling server pusat
            tid = int(os.getenv('TETASCO_ID', 1))
            ctx = _ssl.create_default_context()
            req = _ur.Request(
                f'https://tetasco.my.id/api/tetasco/{tid}/is-claimed',
                headers={'User-Agent': 'TetascoRaspi/1.0', 'Accept': 'application/json'}
            )
            with _ur.urlopen(req, context=ctx, timeout=8) as resp:
                d = _j.loads(resp.read().decode())

            if not d.get('claimed') and _CLAIMED_FILE.exists():
                logger.info('[Unclaim Watcher] Lemari di-unclaim dari HP! Reset & redirect...')
                _CLAIMED_FILE.unlink(missing_ok=True)
                # Paksa Chromium kembali ke halaman pairing
                _sp.Popen(
                    'DISPLAY=:0 pkill -f chromium; sleep 1; '
                    'DISPLAY=:0 chromium '
                    '--start-fullscreen --noerrdialogs --disable-infobars '
                    '--no-first-run --fast --fast-start --disable-translate '
                    '--disable-pinch --overscroll-history-navigation=0 '
                    '--touch-events=enabled '
                    'http://127.0.0.1:5001/pair &',
                    shell=True
                )
                logger.info('[Unclaim Watcher] Chromium diarahkan ke /pair (welcome screen).')

        except Exception as ex:
            logger.debug(f'[Unclaim Watcher] Error: {ex}')'''

if OLD_WATCHER in content:
    content = content.replace(OLD_WATCHER, NEW_WATCHER, 1)
    print('[OK] Watcher diupdate — sekarang restart Chromium saat unclaim', flush=True)
else:
    print('[WARN] Pattern lama tidak ditemukan, cek manual', flush=True)
    r(rs, 'grep -n "_unclaim_watcher_thread\\|Chromium\\|chromium" ~/Penetas-Telur/backend/app.py | head -10',
      'Cek watcher di app.py')

# Upload
sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py diupload', flush=True)

# Restart backend
import time
r(rs, 'pkill -f "backend/app.py" 2>/dev/null; echo killed', 'Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
time.sleep(4)
r(rs, 'tail -5 /tmp/tetasco_backend.log', 'Backend log')

# --- Test langsung: simulasi unclaim dari server ---
print('\n[TEST] Simulasi unclaim sekarang...', flush=True)

# 1. Set claimed dulu
r(rs, 'echo \'{"farm_name":"Test"}\' > ~/.tetasco_claimed', 'Set flag claimed')
r(rs, 'curl -s http://localhost:5001/api/claim-status', 'Status sebelum unclaim')

# 2. Unclaim via endpoint lokal
r(rs, 'curl -s -X POST http://localhost:5001/api/unclaim', 'POST /api/unclaim')

# 3. Cek setelah unclaim
r(rs, 'ls -la ~/.tetasco_claimed 2>/dev/null || echo "Flag TERHAPUS ✓"', 'Flag status')

# 4. Cek proses Chromium (seharusnya restart)
time.sleep(3)
r(rs, 'ps aux | grep chromium | grep -v grep | wc -l', 'Chromium processes')

rs.close()
print('\n✅ Done! Selanjutnya: hapus di HP → tunggu maks 30 detik → LCD otomatis buka /pair', flush=True)
