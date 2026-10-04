import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Baca main.py dari container
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'main.py: {len(main_py)} chars')

# Fix 1: str(tetasco_id) -> tetasco_id  (key di _cam_frames adalah int bukan str)
main_py = main_py.replace(
    'has_camera  = str(tetasco_id) in _cam_frames',
    'has_camera  = tetasco_id in _cam_frames',
    1
)

# Fix 2: nm claims[key] -> farm_name di return block
main_py = main_py.replace(
    '"nm":  claims[key].get("farmName", f"Lemari #{tetasco_id}"),',
    '"nm":  farm_name,',
    1
)

# Fix 3: juga _share_tokens name pakai farm_name bukan claims[key]
# (sudah ada farm_name variable di atas token creation)
main_py = main_py.replace(
    '"name":       (claims.get(key) or {}).get("farmName", f"Lemari #{tetasco_id}"),',
    '"name":       farm_name,',
    1
)

print('[OK] All patches applied')

# Upload ke host file dulu (agar persistent setelah restart container)
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_fix2.py')
sftp.close()
print('[OK] Uploaded ke host + /tmp')

r('docker cp /tmp/main_fix2.py tetasco-backend:/app/main.py && echo copied', '1. Copy ke container')
r('docker restart tetasco-backend 2>&1 | tail -1', '2. Restart', timeout=20)
time.sleep(10)

r('curl -s http://localhost:8000/api/health', '3. Health')

# Cek _cam_frames key type
r("docker exec tetasco-backend python3 -c \"import sys; sys.path.insert(0,'/app'); exec(open('/app/main.py').read().split('from fastapi')[0]); print('ok')\" 2>&1 | head -3", '4. Quick check')

result = r(
    "curl -s -X POST http://localhost:8000/api/tetasco/1/share-token "
    "-H 'Content-Type: application/json' "
    "-d '{\"appId\":\"test\"}'",
    '5. Test share token'
)

if '"token"' in result:
    print('\n🎉 SHARE TOKEN BERHASIL GENERATE!')
else:
    r('docker logs tetasco-backend --tail 10 2>&1', '6. Log error')

sv.close()
