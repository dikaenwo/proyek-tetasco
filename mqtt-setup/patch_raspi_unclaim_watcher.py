"""patch_raspi_unclaim_watcher.py — Tambah background thread di Raspi Flask untuk deteksi unclaim"""
import paramiko, sys, io, time
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

UNCLAIM_WATCHER = '''

# ═══════════════════════════════════════════════════════════════
#  BACKGROUND THREAD: Monitor unclaim dari server pusat
#  Jika Android user hapus lemari → flag lokal dihapus →
#  browser di Raspi redirect ke /pair (welcome screen)
# ═══════════════════════════════════════════════════════════════
import threading as _threading

def _unclaim_watcher_thread():
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
            logger.debug(f'[Unclaim Watcher] Error: {ex}')

# Start watcher thread di background (daemon = mati saat app mati)
_watcher_thread = _threading.Thread(target=_unclaim_watcher_thread, daemon=True, name='unclaim-watcher')
_watcher_thread.start()

'''

# Tambah endpoint /api/unclaim (dipanggil langsung dari Android jika di LAN yang sama)
UNCLAIM_ENDPOINT = '''

@app.route('/api/unclaim', methods=['POST'])
def api_unclaim():
    """
    Dipanggil Android untuk hapus klaim lemari.
    Menghapus flag lokal → browser redirect ke /pair.
    """
    _CLAIMED_FILE.unlink(missing_ok=True)
    logger.info('[Pairing] Lemari di-unclaim via endpoint lokal.')
    return jsonify({'ok': True, 'message': 'Lemari berhasil di-unclaim. Silakan hubungkan ulang.'})

'''

# Cek apakah sudah ada
if '_unclaim_watcher_thread' in content:
    print('[SKIP] Unclaim watcher sudah ada', flush=True)
else:
    # Sisipkan setelah definisi _watcher_thread (setelah mark-claimed endpoint)
    anchor = "# Start watcher thread"
    if anchor in content:
        print('[SKIP] Sudah ada', flush=True)
    else:
        # Sisipkan sebelum if __name__
        content = content.replace('\nif __name__', UNCLAIM_WATCHER + '\nif __name__', 1)
        print('[OK] Unclaim watcher ditambahkan', flush=True)

if '/api/unclaim' in content:
    print('[SKIP] /api/unclaim endpoint sudah ada', flush=True)
else:
    content = content.replace('\nif __name__', UNCLAIM_ENDPOINT + '\nif __name__', 1)
    print('[OK] /api/unclaim endpoint ditambahkan', flush=True)

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print(f'[OK] app.py updated ({len(content)} chars)', flush=True)

# Restart backend
r(rs, 'pkill -f "backend/app.py" 2>/dev/null; echo killed', 'Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Backend restarted', flush=True)
time.sleep(5)

r(rs, 'tail -8 /tmp/tetasco_backend.log', 'Backend log (watcher thread)')
r(rs, 'curl -s -X POST http://localhost:5001/api/unclaim', 'Test /api/unclaim endpoint')
r(rs, 'curl -s http://localhost:5001/api/claim-status', 'claim-status setelah unclaim')

# Cleanup — set ulang claimed untuk normal operation
r(rs, 'echo "Unclaim watcher READY. Thread berjalan di background."')

rs.close()
print('\n✅ Done!', flush=True)
