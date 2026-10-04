"""
deploy_share_feature.py
=======================
Tambah share token endpoints ke server FastAPI (telur):
  POST /api/tetasco/{id}/share-token  → generate token
  GET  /api/join/{token}              → validate + return device info
"""
import paramiko, sys, io, time, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

SHARE_CODE = '''

# ═══════════════════════════════════════════════════════════════════════════════
# SHARE DEVICE — Bagikan akses lemari via QR code
# ═══════════════════════════════════════════════════════════════════════════════
import secrets as _secrets
import time as _share_time

# In-memory store: token -> {tetascoId, name, createdAt, expiresAt}
_share_tokens: dict[str, dict] = {}
_SHARE_TTL    = 72 * 3600  # 72 jam


def _cleanup_tokens():
    now = _share_time.time()
    expired = [t for t, d in _share_tokens.items() if d["expiresAt"] < now]
    for t in expired:
        del _share_tokens[t]


class ShareRequest(BaseModel):
    appId: str


@app.post("/api/tetasco/{tetasco_id}/share-token")
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
        raise HTTPException(status_code=403, detail="Bukan pemilik lemari ini")

    token = _secrets.token_urlsafe(16)
    now   = _share_time.time()
    _share_tokens[token] = {
        "tetascoId":  tetasco_id,
        "name":       claims[key].get("farmName", f"Lemari #{tetasco_id}"),
        "appIdOwner": body.appId,
        "createdAt":  now,
        "expiresAt":  now + _SHARE_TTL,
    }
    logger.info(f"[Share] Token baru untuk lemari-{tetasco_id}")
    return {
        "token":     token,
        "expiresIn": _SHARE_TTL,
        "qrPayload": {
            "t":   "share",
            "id":  tetasco_id,
            "tok": token,
            "nm":  claims[key].get("farmName", f"Lemari #{tetasco_id}"),
            "sv":  "https://tetasco.my.id",
        }
    }


@app.get("/api/join/{token}")
async def join_via_token(token: str):
    """
    HP lain panggil ini setelah scan QR → dapat info device.
    Return: device info lengkap yang bisa disimpan di appStore.
    """
    _cleanup_tokens()
    info = _share_tokens.get(token)
    if not info:
        raise HTTPException(status_code=404, detail="Token tidak valid atau sudah kadaluarsa")
    if _share_time.time() > info["expiresAt"]:
        del _share_tokens[token]
        raise HTTPException(status_code=410, detail="Token sudah kadaluarsa")

    tid = info["tetascoId"]
    did = device_id_from_tetasco_id(tid)
    hb  = heartbeat_cache.get(did, {})
    sensor = device_sensor_cache.get(did, {})
    now_ts = int(_share_time.time())
    online = bool(hb.get("ts") and (now_ts - hb["ts"]) < 120)

    return {
        "ok":         True,
        "tetascoId":  tid,
        "deviceId":   did,
        "name":       info["name"],
        "serverUrl":  "https://tetasco.my.id",
        "online":     online,
        "temperature": sensor.get("temperature"),
        "humidity":    sensor.get("humidity"),
        "sharedAccess": True,
        "expiresAt":  info["expiresAt"],
        "remainingHours": round((info["expiresAt"] - _share_time.time()) / 3600, 1),
    }


@app.delete("/api/join/{token}")
async def revoke_share_token(token: str, appId: str = ""):
    """Pemilik bisa revoke token kapan saja."""
    info = _share_tokens.get(token)
    if not info:
        raise HTTPException(status_code=404, detail="Token tidak ditemukan")
    if info.get("appIdOwner") != appId:
        raise HTTPException(status_code=403, detail="Bukan pemilik token")
    del _share_tokens[token]
    return {"ok": True, "message": "Token dicabut"}

'''

if '/api/join/' in main_py:
    print('[INFO] Share endpoints sudah ada')
else:
    main_py = main_py.rstrip() + '\n' + SHARE_CODE
    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.close()
    print('[OK] Share endpoints ditambahkan')

# Rebuild backend
r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -3', '1. Build backend', timeout=120)
r('cd ~/tetasco-connect && docker compose up -d backend 2>&1 | tail -5', '2. Restart backend', timeout=30)
time.sleep(10)
r('curl -s http://localhost:8000/api/health', '3. Health check')

# Test share token endpoint
r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"test123"}\'', '4. Test share endpoint (expected 403)')

sv.close()
print('\n✅ Server share endpoints deployed!')
