"""implement_claim_api.py — Tambah Claim API ke main.py di container server"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# Baca main.py dari container
r(cs, 'docker cp tetasco-backend:/app/main.py /home/telur/tetasco-connect/backend/main.py_backup', 'Backup')
i, o, e = cs.exec_command('cat /home/telur/tetasco-connect/backend/main.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] main.py: {len(content)} chars', flush=True)

# ─── Code yang akan ditambahkan ───────────────────────────────
CLAIM_CODE = '''
# ═══════════════════════════════════════════════════════════════
#  CLAIM SYSTEM — Multi-Tenant Device Ownership (tanpa akun)
# ═══════════════════════════════════════════════════════════════
import hmac, hashlib, json
from pathlib import Path

CLAIM_MASTER_KEY = os.getenv("CLAIM_MASTER_KEY", "tetasco-secret-2026")
CLAIMS_FILE      = Path("/app/claims.json")

def _load_claims() -> dict:
    if CLAIMS_FILE.exists():
        try:
            return json.loads(CLAIMS_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_claims(data: dict):
    CLAIMS_FILE.write_text(json.dumps(data, indent=2))

def get_claim_token(tetasco_id: int) -> str:
    """Generate deterministic claim token dari tetascoId + master key."""
    msg = f"lemari-{tetasco_id}".encode()
    key = CLAIM_MASTER_KEY.encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:8].upper()

# ── Endpoints ──────────────────────────────────────────────────

@app.post("/api/claim")
async def claim_device(request: Request):
    """
    Peternak klaim lemari setelah scan QR.
    Body: {tetascoId, claimToken, appId, farmName?}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    tetasco_id  = int(body.get("tetascoId", 0))
    claim_token = str(body.get("claimToken", "")).upper().strip()
    app_id      = str(body.get("appId", "")).strip()
    farm_name   = str(body.get("farmName", f"Lemari #{tetasco_id}"))

    if not tetasco_id or not claim_token or not app_id:
        raise HTTPException(400, "tetascoId, claimToken, dan appId wajib diisi")

    # Verifikasi token
    expected = get_claim_token(tetasco_id)
    if not hmac.compare_digest(claim_token, expected):
        raise HTTPException(403, "Token tidak valid — scan QR dari monitor lemari yang benar")

    # Simpan klaim
    claims = _load_claims()
    device_key = str(tetasco_id)
    claims[device_key] = {
        "tetascoId": tetasco_id,
        "appId":     app_id,
        "farmName":  farm_name,
        "claimedAt": int(__import__("time").time()),
    }
    _save_claims(claims)

    device_id = device_id_from_tetasco_id(tetasco_id)
    logger.info(f"[Claim] lemari-{tetasco_id} diklaim oleh appId={app_id[:8]}...")
    return {
        "ok":       True,
        "deviceId": device_id,
        "name":     farm_name,
        "message":  f"Berhasil! {farm_name} sekarang terhubung ke app Anda.",
    }


@app.get("/api/my-devices")
async def my_devices(appId: str = ""):
    """
    Daftar semua lemari yang diklaim oleh appId ini.
    Query: ?appId=<uuid>
    """
    if not appId:
        raise HTTPException(400, "appId wajib diisi")

    claims = _load_claims()
    result = []
    for device_key, claim in claims.items():
        if claim.get("appId") != appId:
            continue
        tid = claim["tetascoId"]
        device_id = device_id_from_tetasco_id(tid)
        # Gabungkan dengan data real-time
        sensor  = device_sensor_cache.get(device_id, {})
        status  = device_status_cache.get(device_id, {})
        hb      = heartbeat_cache.get(device_id, {})
        online  = bool(hb.get("ts") and (int(__import__("time").time()) - hb["ts"]) < 120)
        result.append({
            "tetascoId":   tid,
            "deviceId":    device_id,
            "name":        claim.get("farmName", f"Lemari #{tid}"),
            "claimedAt":   claim.get("claimedAt"),
            "online":      online,
            "temperature": sensor.get("temperature"),
            "humidity":    sensor.get("humidity"),
            "ip":          hb.get("ip"),
        })
    return {"total": len(result), "devices": result}


@app.delete("/api/claim/{tetasco_id}")
async def unclaim_device(tetasco_id: int, appId: str = ""):
    """Lepaskan klaim lemari (unclaim)."""
    if not appId:
        raise HTTPException(400, "appId wajib diisi")

    claims = _load_claims()
    device_key = str(tetasco_id)
    if device_key not in claims:
        raise HTTPException(404, "Lemari tidak ditemukan dalam klaim")
    if claims[device_key].get("appId") != appId:
        raise HTTPException(403, "Lemari ini bukan milik appId Anda")

    del claims[device_key]
    _save_claims(claims)
    logger.info(f"[Claim] lemari-{tetasco_id} di-unclaim oleh appId={appId[:8]}...")
    return {"ok": True, "message": f"Lemari #{tetasco_id} berhasil dilepas"}


@app.get("/api/tetasco/{tetasco_id}/claim-token")
async def get_device_claim_token(tetasco_id: int):
    """
    Untuk Raspi: ambil claim token agar bisa generate QR.
    Response: {token, qrData}
    """
    token   = get_claim_token(tetasco_id)
    qr_data = f"tetasco://claim?id={tetasco_id}&token={token}"
    return {
        "tetascoId": tetasco_id,
        "token":     token,
        "qrData":    qr_data,
    }
'''

# Tambahkan sebelum baris if __name__ == "__main__" atau di akhir file
# Cek apakah sudah ada
if '/api/claim' in content:
    print('[SKIP] Claim API sudah ada di main.py', flush=True)
else:
    # Tambah import os jika belum ada
    if 'import os' not in content:
        content = content.replace('from fastapi import', 'import os\nfrom fastapi import', 1)
    
    # Tambah CLAIM_CODE sebelum baris terakhir (if __name__)
    if 'if __name__' in content:
        content = content.replace('if __name__', CLAIM_CODE + '\nif __name__')
    else:
        content += CLAIM_CODE
    
    # Tulis ke host
    sftp = cs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.close()
    
    # docker cp ke container
    r(cs, 'docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo "docker cp OK"',
      '1. docker cp main.py')
    
    # Restart
    r(cs, 'docker restart tetasco-backend && sleep 8', '2. Restart container')
    
    print('[OK] Claim API ditambahkan!', flush=True)

# Test endpoints baru
import time; time.sleep(3)

r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -m json.tool',
  '3. Test claim-token endpoint')

r(cs, '''curl -s -X POST http://localhost:8000/api/claim \
    -H "Content-Type: application/json" \
    -d \'{"tetascoId":1,"claimToken":"WRONGTOKEN","appId":"test-app-id","farmName":"Test Farm"}\' | python3 -m json.tool''',
  '4. Test claim dengan token salah (harus 403)')

# Dapat token dulu, lalu test claim
i2, o2, e2 = cs.exec_command('curl -s http://localhost:8000/api/tetasco/1/claim-token')
import json as _json
token_resp = _json.loads(o2.read().decode())
valid_token = token_resp.get('token', '')
print(f'\n[INFO] Valid token untuk lemari-1: {valid_token}', flush=True)

r(cs, f'''curl -s -X POST http://localhost:8000/api/claim \
    -H "Content-Type: application/json" \
    -d \'{{"tetascoId":1,"claimToken":"{valid_token}","appId":"test-phone-uuid-123","farmName":"Kandang Dika"}}\' | python3 -m json.tool''',
  '5. Test claim dengan token benar (harus OK)')

r(cs, 'curl -s "http://localhost:8000/api/my-devices?appId=test-phone-uuid-123" | python3 -m json.tool',
  '6. Test my-devices (harus return lemari-1)')

cs.close()
print('\n✅ Done!', flush=True)
