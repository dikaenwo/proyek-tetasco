"""finalize_pairing.py — (1) Update startup Raspi ke /pair, (2) tambah is-claimed di server, (3) update claim-status endpoint Raspi"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Server Pusat ─────────────────────────────────────────────────────────────
cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Tambah endpoint is-claimed ke main.py server
IS_CLAIMED_ENDPOINT = '''

@app.get("/api/tetasco/{tetasco_id}/is-claimed")
async def is_device_claimed(tetasco_id: int):
    """Cek apakah lemari sudah diklaim oleh siapapun (tanpa butuh appId)."""
    claims = _load_claims()
    claim = claims.get(str(tetasco_id))
    if claim:
        return {"claimed": True, "farm_name": claim.get("farmName", f"Lemari #{tetasco_id}"), "claimedAt": claim.get("claimedAt")}
    return {"claimed": False}

'''

i, o, e = cs.exec_command('cat /home/telur/tetasco-connect/backend/main.py')
content = o.read().decode('utf-8', 'replace')

if 'is-claimed' in content:
    print('[SKIP] is-claimed endpoint sudah ada', flush=True)
else:
    # Tambah sebelum if __name__
    content = content.replace('if __name__', IS_CLAIMED_ENDPOINT + '\nif __name__', 1)
    sftp = cs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.close()
    r(cs, 'docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && docker restart tetasco-backend && sleep 10',
      'Server: Deploy is-claimed endpoint')
    print('[OK] is-claimed endpoint added', flush=True)

time.sleep(3)
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/is-claimed | python3 -m json.tool', 'Test is-claimed')
cs.close()

# ── Raspi ─────────────────────────────────────────────────────────────────────
rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

# (A) Update claim-status di Raspi untuk poll central server
i2, o2, e2 = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_content = o2.read().decode('utf-8', 'replace')

OLD_CLAIM_STATUS = '''@app.route('/api/claim-status')
def api_claim_status():
    """Cek apakah lemari sudah diklaim."""
    if _CLAIMED_FILE.exists():
        try:
            data = _json.loads(_CLAIMED_FILE.read_text())
            return jsonify({'claimed': True, 'farm_name': data.get('farm_name', 'Lemari Saya')})
        except:
            return jsonify({'claimed': True, 'farm_name': 'Lemari Saya'})
    return jsonify({'claimed': False})'''

NEW_CLAIM_STATUS = '''@app.route('/api/claim-status')
def api_claim_status():
    """Cek apakah lemari sudah diklaim (lokal + polling central server)."""
    # 1. Cek flag lokal
    if _CLAIMED_FILE.exists():
        try:
            data = _json.loads(_CLAIMED_FILE.read_text())
            return jsonify({'claimed': True, 'farm_name': data.get('farm_name', 'Lemari Saya')})
        except:
            return jsonify({'claimed': True, 'farm_name': 'Lemari Saya'})

    # 2. Poll central server
    try:
        import requests as _req
        tid   = int(os.getenv('TETASCO_ID', 1))
        resp  = _req.get(f'https://tetasco.my.id/api/tetasco/{tid}/is-claimed', timeout=5)
        if resp.ok:
            d = resp.json()
            if d.get('claimed'):
                # Simpan lokal
                _CLAIMED_FILE.write_text(_json.dumps({'farm_name': d.get('farm_name', 'Lemari Saya')}))
                return jsonify({'claimed': True, 'farm_name': d.get('farm_name', 'Lemari Saya')})
    except Exception as ex:
        logger.debug(f'Claim status poll error: {ex}')

    return jsonify({'claimed': False})'''

if NEW_CLAIM_STATUS[:50] in app_content:
    print('[SKIP] claim-status sudah diupdate', flush=True)
elif OLD_CLAIM_STATUS in app_content:
    app_content = app_content.replace(OLD_CLAIM_STATUS, NEW_CLAIM_STATUS, 1)
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(app_content.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
    sftp.close()
    print('[OK] claim-status updated (poll central server)', flush=True)
else:
    print('[WARN] OLD pattern tidak ditemukan, skip update claim-status', flush=True)

# (B) Update startup script: Chromium buka /pair bukan /
i3, o3, e3 = rs.exec_command('cat ~/Penetas-Telur/scripts/start_tetasco.sh')
sh_content = o3.read().decode('utf-8','replace')

if 'http://127.0.0.1:5001/pair' in sh_content:
    print('[SKIP] Startup sudah /pair', flush=True)
else:
    sh_content = sh_content.replace('http://127.0.0.1:5001', 'http://127.0.0.1:5001/pair', 1)
    sftp = rs.open_sftp()
    sftp.putfo(io.BytesIO(sh_content.encode()), '/home/tetasco1/Penetas-Telur/scripts/start_tetasco.sh')
    sftp.close()
    print('[OK] Startup script → /pair', flush=True)

# (C) Restart backend Raspi
rs.exec_command('pkill -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
time.sleep(4)

r(rs, 'curl -s http://localhost:5001/api/claim-status', 'Raspi claim-status (poll server)')

# (D) Chromium reload ke /pair
r(rs, '''pkill -f chromium 2>/dev/null; sleep 2
DISPLAY=:0 chromium \\
    --start-fullscreen --noerrdialogs --disable-infobars \\
    --no-first-run --fast --fast-start --disable-translate \\
    --disable-pinch --overscroll-history-navigation=0 \\
    --touch-events=enabled \\
    --window-size=1024,600 --window-position=0,0 \\
    http://127.0.0.1:5001/pair &
echo "Chromium opened at /pair"''', 'Buka Chromium ke /pair')

rs.close()
print('\n✅ All done! Monitor HDMI sekarang menampilkan welcome page Tetasco.', flush=True)
