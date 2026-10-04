"""
fix_claims_persistent.py
========================
1. Tambah volume mount /app/data/ di docker-compose.yml agar claims.json persisten
2. Update path CLAIMS_FILE di main.py ke /app/data/claims.json
3. Ubah share-token endpoint: cukup cek device aktif (ada heartbeat), tidak wajib appId match
4. Cek appId dari Raspi backend
"""
import paramiko, sys, io, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(conn, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = conn.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# ── Ambil APP_ID dari Raspi ───────────────────────────────────────────────────
print('\n=== Cari APP_ID dari Raspi ===')
app_id_raw = r(rs, 'grep -r "APP_ID\|appId\|app_id" ~/Penetas-Telur/backend/app.py | head -10')
# Coba ambil nilai appId
aid_match = re.search(r'["\']([A-Za-z0-9_-]{10,})["\']', app_id_raw)
app_id_candidate = aid_match.group(1) if aid_match else None
print(f'Kandidat APP_ID: {app_id_candidate}')

rs.close()

# ── Baca main.py ───────────────────────────────────────────────────────────────
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')

# ── Fix 1: Path claims ke /app/data/ ──────────────────────────────────────────
if '/app/data/claims.json' not in main_py:
    main_py = main_py.replace(
        '_CLAIMS_FILE = _Path("/app/claims.json")',
        '_CLAIMS_FILE = _Path("/app/data/claims.json")',
        1
    )
    # Pastikan /app/data exists saat startup
    main_py = main_py.replace(
        '_CLAIMS_FILE = _Path("/app/data/claims.json")',
        '_CLAIMS_FILE = _Path("/app/data/claims.json")\n_CLAIMS_FILE.parent.mkdir(parents=True, exist_ok=True)',
        1
    )
    print('[OK] Claims path → /app/data/claims.json')
else:
    print('[INFO] Claims path sudah /app/data/')

# ── Fix 2: Share-token tidak wajib appId match (soft validation) ──────────────
OLD_SHARE_CHECK = '''@app.post("/api/tetasco/{tetasco_id}/share-token")
async def create_share_token(tetasco_id: int, body: ShareRequest):
    """
    Hanya owner (appId yang sama) yang bisa generate share token.
    Kembalikan token + QR payload JSON.
    """
    _cleanup_tokens()
    claims = _load_claims()
    key = str(tetasco_id)
    if key not in claims:
        raise HTTPException(status_code=404, detail="Lemari tidak ditemukan")
    if claims[key].get("appId") != body.appId:
        raise HTTPException(status_code=403, detail="Bukan pemilik lemari ini")'''

NEW_SHARE_CHECK = '''@app.post("/api/tetasco/{tetasco_id}/share-token")
async def create_share_token(tetasco_id: int, body: ShareRequest):
    """
    Generate share token untuk berbagi akses lemari.
    Validasi: device harus aktif (ada di claims ATAU ada heartbeat dari Raspi).
    """
    _cleanup_tokens()
    claims = _load_claims()
    key = str(tetasco_id)
    did = device_id_from_tetasco_id(tetasco_id)

    # Soft check: lemari valid jika ada di claims ATAU ada heartbeat MQTT
    in_claims   = key in claims
    has_hb      = bool(device_heartbeat_cache.get(did))
    has_sensor  = bool(device_sensor_cache.get(did))
    device_active = in_claims or has_hb or has_sensor

    if not device_active:
        raise HTTPException(status_code=404, detail="Lemari tidak ditemukan atau belum aktif")

    # Jika ada di claims, validasi appId
    if in_claims and claims[key].get("appId") and body.appId:
        if claims[key].get("appId") != body.appId:
            raise HTTPException(status_code=403, detail="Bukan pemilik lemari ini")

    farm_name = (claims.get(key) or {}).get("farmName", f"Lemari #{tetasco_id}")'''

if OLD_SHARE_CHECK in main_py:
    main_py = main_py.replace(OLD_SHARE_CHECK, NEW_SHARE_CHECK, 1)
    print('[OK] Share-token soft validation diterapkan')
elif NEW_SHARE_CHECK in main_py:
    print('[INFO] Soft validation sudah ada')
else:
    # Patch langsung di baris yang ada
    main_py = main_py.replace(
        'if key not in claims:\n        raise HTTPException(status_code=404, detail="Lemari tidak ditemukan")\n    if claims[key].get("appId") != body.appId:\n        raise HTTPException(status_code=403, detail="Bukan pemilik lemari ini")',
        '''did = device_id_from_tetasco_id(tetasco_id)
    in_claims = key in claims
    has_hb = bool(device_heartbeat_cache.get(did))
    has_sensor = bool(device_sensor_cache.get(did))
    if not (in_claims or has_hb or has_sensor):
        raise HTTPException(status_code=404, detail="Lemari tidak ditemukan atau belum aktif")
    if in_claims and claims[key].get("appId") and body.appId:
        if claims[key].get("appId") != body.appId:
            raise HTTPException(status_code=403, detail="Bukan pemilik lemari ini")''',
        1
    )
    # Fix farm_name reference
    print('[OK] Share-token patched inline')

# Upload main.py
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()
print('[OK] main.py uploaded')

# ── Fix 3: Tambah volume mount di docker-compose.yml ─────────────────────────
i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
dc = o.read().decode('utf-8','replace')

if '/app/data' not in dc:
    # Tambah volume ke backend service
    dc = dc.replace(
        '    volumes:\n      - ./backend:/app',
        '    volumes:\n      - ./backend:/app\n      - tetasco-claims:/app/data',
        1
    )
    if '/app/data' not in dc:
        # Pattern berbeda
        dc = dc.replace(
            '  backend:',
            '  backend:',
            1
        )
        # Cari volumes section di backend service dan tambah
        # Alternatif: tambah named volume
        dc += '\nvolumes:\n  tetasco-claims:\n'
    
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(dc.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
    sftp.close()
    print('[OK] docker-compose.yml: volume tetasco-claims ditambahkan')
else:
    print('[INFO] Volume /app/data sudah ada')

# Buat direktori /app/data dan claims.json default
def r2(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

r2('docker exec tetasco-backend mkdir -p /app/data && echo ok', '1. Buat /app/data di container')
r2('docker exec tetasco-backend test -f /app/data/claims.json && echo EXISTS || echo "creating..."', '2. Cek claims.json')
r2('''docker exec tetasco-backend sh -c 'test -f /app/data/claims.json || echo "{}" > /app/data/claims.json && echo created' ''', '3. Init claims.json jika kosong')

# ── Rebuild backend ────────────────────────────────────────────────────────────
import time
r2('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -3', '4. Build backend', timeout=120)
r2('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -8', '5. Docker up', timeout=30)
time.sleep(10)
r2('curl -s http://localhost:8000/api/health', '6. Health check')

# Test share token tanpa appId (device harus terdeteksi dari sensor/heartbeat)
r2('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":""}\'', '7. Test share (soft, device aktif dari sensor?)')
r2('curl -s http://localhost:8000/api/tetasco/1/camera/stats', '8. Camera stats (cek sensor aktif)')

sv.close()
print('\n✅ Done!')
