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

# Baca main.py dari container (yang sudah direbuild)
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Lihat sekitar baris 560-580
lines = main_py.split('\n')
print('[Context baris 555-585]:')
for i2, l in enumerate(lines[555:585], 556):
    print(f'{i2}: {l}')

# Fix 1: claims[key].get("farmName" → safe access
main_py = main_py.replace(
    '"name":       claims[key].get("farmName", f"Lemari #{tetasco_id}"),',
    '"name":       (claims.get(key) or {}).get("farmName", f"Lemari #{tetasco_id}"),',
    1
)

# Fix 2: "appIdOwner": body.appId, → tambahkan
# Pastikan farm_name variable ada sebelum dipakai
if 'farm_name = (claims.get(key) or {}).get' not in main_py:
    # Tambahkan farm_name assignment sebelum token creation
    main_py = main_py.replace(
        'token = _secrets.token_urlsafe(16)',
        'farm_name = (claims.get(key) or {}).get("farmName", f"Lemari #{tetasco_id}")\n    token = _secrets.token_urlsafe(16)',
        1
    )
    print('[OK] farm_name variable ditambahkan')

# Fix 3: ganti semua sisa claims[key] di share endpoint dengan safe access
main_py = main_py.replace(
    'claims[key].get("farmName"',
    '(claims.get(key) or {}).get("farmName"',
)

print(f'\n[INFO] main.py: {len(main_py)} chars')

# Upload ke server host (bukan container) dan rebuild
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()
print('[OK] main.py uploaded ke server host')

# Copy langsung ke container yang jalan (instant fix tanpa rebuild)
sftp2 = sv.open_sftp()
sftp2.putfo(io.BytesIO(main_py.encode()), '/tmp/main_fixed.py')
sftp2.close()
r('docker cp /tmp/main_fixed.py tetasco-backend:/app/main.py && echo "copied"', '1. Copy ke container')

# Restart uvicorn (kill PID 1 = graceful reload di uvicorn)
r('docker exec tetasco-backend kill -SIGTERM 1 2>/dev/null || true; sleep 2; docker restart tetasco-backend 2>&1 | tail -1', '2. Restart container', timeout=25)
time.sleep(10)

# Test
r('curl -s http://localhost:8000/api/health', '3. Health')
result = r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"test"}\'', '4. Test share token')

if 'token' in result:
    print('\n🎉 SHARE TOKEN BERHASIL!')
elif 'error' in result.lower() or 'Error' in result:
    print('\n❌ Masih error, cek log:')
    r('docker logs tetasco-backend --tail 15 2>&1', '5. Backend log error')

sv.close()
