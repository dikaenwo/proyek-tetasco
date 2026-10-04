"""fix_main_final.py — Fix import + inject claim API ke main.py dari backup"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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

# ── Baca dari BACKUP yang benar ──────────────────────────────────────────────
i, o, e = cs.exec_command('cat /home/telur/tetasco-connect/backend/main.py_backup')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] Backup: {len(content)} chars', flush=True)

# Cek baris FastAPI import
for line in content.split('\n'):
    if 'from fastapi import' in line:
        print(f'[IMPORT] {line.strip()}', flush=True)
        break

# ── Fix 1: Tambah Request ke import ──────────────────────────────────────────
OLD_IMPORT = 'from fastapi import FastAPI, HTTPException, Depends'
NEW_IMPORT = 'from fastapi import FastAPI, HTTPException, Depends, Request'
if OLD_IMPORT in content:
    content = content.replace(OLD_IMPORT, NEW_IMPORT, 1)
    print('[FIX] Tambah Request ke import', flush=True)
elif 'Request' in content:
    print('[OK] Request sudah ada', flush=True)
else:
    # Fallback: tambah di baris paling atas
    content = 'from fastapi import Request\n' + content
    print('[FIX] Tambah import Request di atas', flush=True)

# ── Fix 2: Inject Claim API (jika belum ada) ─────────────────────────────────
if '/api/claim' in content:
    print('[SKIP] Claim API sudah ada', flush=True)
else:
    CLAIM_CODE = '''

# ══════════════════════════════════════════════════════════════════════════════
#  CLAIM SYSTEM — Multi-Tenant, tanpa akun, verifikasi via QR Raspi
# ══════════════════════════════════════════════════════════════════════════════
import hmac as _hmac
import hashlib as _hashlib
import json as _json
from pathlib import Path as _Path

_CLAIM_KEY   = os.getenv("CLAIM_MASTER_KEY", "tetasco-secret-2026")
_CLAIMS_FILE = _Path("/app/claims.json")

def _load_claims() -> dict:
    if _CLAIMS_FILE.exists():
        try:
            return _json.loads(_CLAIMS_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_claims(data: dict):
    _CLAIMS_FILE.write_text(_json.dumps(data, indent=2))

def get_claim_token(tetasco_id: int) -> str:
    msg = f"lemari-{tetasco_id}".encode()
    key = _CLAIM_KEY.encode()
    return _hmac.new(key, msg, _hashlib.sha256).hexdigest()[:8].upper()


@app.get("/api/tetasco/{tetasco_id}/claim-token")
async def claim_token_endpoint(tetasco_id: int):
    token   = get_claim_token(tetasco_id)
    qr_data = f"tetasco://claim?id={tetasco_id}&token={token}"
    return {"tetascoId": tetasco_id, "token": token, "qrData": qr_data}


@app.post("/api/claim")
async def claim_device(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    tetasco_id  = int(body.get("tetascoId", 0))
    claim_token = str(body.get("claimToken", "")).upper().strip()
    app_id      = str(body.get("appId", "")).strip()
    farm_name   = str(body.get("farmName", f"Lemari #{tetasco_id}"))
    if not tetasco_id or not claim_token or not app_id:
        raise HTTPException(status_code=400, detail="tetascoId, claimToken, appId wajib")
    expected = get_claim_token(tetasco_id)
    if not _hmac.compare_digest(claim_token, expected):
        raise HTTPException(status_code=403, detail="Token tidak valid")
    claims = _load_claims()
    claims[str(tetasco_id)] = {"tetascoId": tetasco_id, "appId": app_id, "farmName": farm_name, "claimedAt": int(__import__("time").time())}
    _save_claims(claims)
    logger.info(f"[Claim] lemari-{tetasco_id} by appId={app_id[:8]}...")
    return {"ok": True, "deviceId": f"lemari-{tetasco_id}", "name": farm_name, "message": f"Berhasil! {farm_name} terhubung."}


@app.get("/api/my-devices")
async def my_devices(appId: str = ""):
    if not appId:
        raise HTTPException(status_code=400, detail="appId wajib")
    claims  = _load_claims()
    result  = []
    now_ts  = int(__import__("time").time())
    for device_key, claim in claims.items():
        if claim.get("appId") != appId:
            continue
        tid = claim["tetascoId"]
        did = device_id_from_tetasco_id(tid)
        hb  = heartbeat_cache.get(did, {})
        sensor = device_sensor_cache.get(did, {})
        online = bool(hb.get("ts") and (now_ts - hb["ts"]) < 120)
        result.append({"tetascoId": tid, "deviceId": did, "name": claim.get("farmName", f"Lemari #{tid}"), "claimedAt": claim.get("claimedAt"), "online": online, "temperature": sensor.get("temperature"), "humidity": sensor.get("humidity"), "ip": hb.get("ip")})
    return {"total": len(result), "devices": result}


@app.delete("/api/claim/{tetasco_id}")
async def unclaim_device(tetasco_id: int, appId: str = ""):
    if not appId:
        raise HTTPException(status_code=400, detail="appId wajib")
    claims = _load_claims()
    key = str(tetasco_id)
    if key not in claims:
        raise HTTPException(status_code=404, detail="Lemari tidak ditemukan")
    if claims[key].get("appId") != appId:
        raise HTTPException(status_code=403, detail="Bukan lemari Anda")
    del claims[key]
    _save_claims(claims)
    return {"ok": True, "message": f"Lemari #{tetasco_id} dilepas"}

'''
    # Sisipkan sebelum blok if __name__
    if 'if __name__' in content:
        content = content.replace('if __name__', CLAIM_CODE + '\nif __name__', 1)
    else:
        content += CLAIM_CODE
    print('[OK] Claim API ditambahkan', flush=True)

# ── Tulis ke host ─────────────────────────────────────────────────────────────
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()
print(f'[OK] main.py ditulis ({len(content)} chars)', flush=True)

# ── Docker cp + restart ───────────────────────────────────────────────────────
r(cs, 'docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo "cp OK"',
  'docker cp')

# Cek postgres juga
r(cs, 'docker ps -a | grep postgres', 'Postgres status')
r(cs, 'docker restart tetasco-postgres tetasco-backend && sleep 15', 'Restart both')
r(cs, 'docker ps --format "{{.Names}} {{.Status}}" | grep -E "backend|postgres"', 'Status setelah restart')
r(cs, 'docker logs tetasco-backend 2>&1 | tail -5', 'Backend logs')

import time; time.sleep(3)

# ── Test ──────────────────────────────────────────────────────────────────────
r(cs, 'curl -s http://localhost:8000/api/health', 'Health')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -m json.tool', 'Claim token lemari-1')
r(cs, 'curl -s http://localhost:8000/api/tetasco/3/claim-token | python3 -m json.tool', 'Claim token lemari-3')

cs.close()
print('\n✅ Done!', flush=True)
