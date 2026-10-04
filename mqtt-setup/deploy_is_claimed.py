"""deploy_is_claimed.py — Tambah is-claimed endpoint ke server pusat"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl='', timeout=60):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Baca main.py dari DALAM container (bukan host)
print('[1. Baca main.py dari container]', flush=True)
i, o, e = cs.exec_command('docker exec tetasco-backend cat /app/main.py')
content = o.read().decode('utf-8', 'replace')
print(f'    → {len(content)} chars', flush=True)

if not content:
    print('[ERR] Tidak bisa baca main.py dari container', flush=True)
    cs.close(); exit(1)

if 'is-claimed' in content:
    print('[SKIP] Endpoint sudah ada', flush=True)
else:
    # Cari anchor: setelah endpoint claim-token
    IS_CLAIMED = '''

@app.get("/api/tetasco/{tetasco_id}/is-claimed")
async def is_device_claimed(tetasco_id: int):
    """Cek apakah lemari sudah diklaim oleh siapapun (tanpa butuh appId)."""
    claims = _load_claims()
    claim  = claims.get(str(tetasco_id))
    if claim:
        return {
            "claimed":   True,
            "farm_name": claim.get("farmName", f"Lemari #{tetasco_id}"),
            "claimed_at": claim.get("claimedAt"),
        }
    return {"claimed": False}

'''
    # Sisipkan setelah fungsi claim-token
    if 'claim-token' in content:
        # Temukan akhir fungsi claim-token
        idx = content.find('@app.get("/api/tetasco/{tetasco_id}/claim-token")')
        # Cari akhir fungsi (baris berikutnya yang dimulai dengan @app atau akhir file)
        next_route = content.find('\n@app.', idx + 50)
        if next_route > 0:
            content = content[:next_route] + IS_CLAIMED + content[next_route:]
        else:
            # Tambah di akhir sebelum if __name__
            content = content.replace('if __name__', IS_CLAIMED + '\nif __name__', 1)
    else:
        content = content + IS_CLAIMED

    # Tulis ke /tmp dulu
    sftp = cs.open_sftp()
    sftp.putfo(io.BytesIO(content.encode()), '/tmp/main_patched.py')
    sftp.close()
    print('[2. File ditulis ke /tmp/main_patched.py]', flush=True)

    # Copy ke container
    r(cs, 'docker cp /tmp/main_patched.py tetasco-backend:/app/main.py', '3. docker cp ke container')

    # Restart container
    r(cs, 'docker restart tetasco-backend', '4. Restart container', timeout=30)

    import time; time.sleep(8)

# Test
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/is-claimed', '5. Test is-claimed')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token', '6. Test claim-token (existing)')

# Test klaim saat ini
r(cs, 'curl -s http://localhost:8000/api/my-devices?appId=test-debug | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'Devices: {d.get(chr(116)+chr(111)+chr(116)+chr(97)+chr(108))}\');" 2>/dev/null || true',
  '7. my-devices check')

cs.close()
print('\n✅ Done!', flush=True)
