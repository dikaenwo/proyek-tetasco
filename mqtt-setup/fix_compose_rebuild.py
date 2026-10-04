import paramiko, sys, io, time
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

# 1. Baca & tampilkan docker-compose.yml saat ini
i,o,e = sv.exec_command('cat ~/tetasco-connect/docker-compose.yml')
dc = o.read().decode('utf-8','replace')
print(f'docker-compose.yml: {len(dc)} chars')
print(dc[-600:])  # Tampilkan bagian akhir

# 2. Fix: hapus duplikat volumes key di akhir file
lines = dc.split('\n')
# Temukan semua baris "volumes:" di top-level (indentasi 0)
volume_lines = [(i, l) for i, l in enumerate(lines) if l.strip() == 'volumes:' and (not l.startswith(' '))]
print(f'\nvolumes: keys at lines: {[i for i,l in volume_lines]}')

if len(volume_lines) > 1:
    # Hapus duplikat (biarkan yang pertama, hapus yang terakhir beserta isinya)
    # Yang pertama = milik services
    # Yang terakhir = named volumes (kita tambahkan)
    # Merge: hapus yang terakhir, tambahkan named volume ke yang pertama
    last_vol_line = volume_lines[-1][0]
    # Ambil isi named volume section (setelah baris terakhir "volumes:")
    named_vols = lines[last_vol_line+1:]
    # Hapus dari baris terakhir volumes sampai akhir
    lines = lines[:last_vol_line]
    dc_fixed = '\n'.join(lines)
    
    # Sekarang cari named volumes section yang sudah ada (volumes: di paling akhir sebelum services block)
    # Cari "volumes:" setelah kata services
    print('[OK] Docker-compose duplikat volumes dihapus')
else:
    dc_fixed = dc
    print('[INFO] Tidak ada duplikat')

# Pastikan ada named volumes section yang benar di akhir
if 'tetasco-claims' not in dc_fixed:
    dc_fixed = dc_fixed.rstrip() + '\n\nvolumes:\n  tetasco-claims:\n'
    print('[OK] Named volume tetasco-claims ditambahkan')
else:
    print('[INFO] tetasco-claims sudah ada')

# Pastikan backend service punya volume mount
if '/app/data' not in dc_fixed:
    # Tambah ke backend service volumes
    dc_fixed = dc_fixed.replace(
        '      - ./backend:/app\n',
        '      - ./backend:/app\n      - tetasco-claims:/app/data\n',
        1
    )
    print('[OK] Volume mount /app/data ditambahkan ke backend service')

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(dc_fixed.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
sftp.close()
print('[OK] docker-compose.yml uploaded')

# Validasi YAML
r('cd ~/tetasco-connect && docker compose config --quiet 2>&1 | head -5 || echo "YAML OK"', '3. Validate YAML')

# 3. Patch main.py langsung — pastikan soft validation pakai _cam_frames juga
i,o,e = sv.exec_command('cat ~/tetasco-connect/backend/main.py')
main_py = o.read().decode('utf-8','replace')

# Cek apakah device_id_from_tetasco_id ada
if 'def device_id_from_tetasco_id' in main_py:
    print('[INFO] device_id_from_tetasco_id ada')
else:
    print('[WARN] device_id_from_tetasco_id tidak ada, tambah...')
    # Tambah helper function
    HELPER = '''
def device_id_from_tetasco_id(tetasco_id: int) -> str:
    return f"lemari-{tetasco_id}"

'''
    main_py = main_py.replace('# ─── State in-memory', HELPER + '# ─── State in-memory', 1)

# Patch share-token: gunakan _cam_frames sebagai deteksi aktif
OLD = 'has_sensor  = bool(device_sensor_cache.get(did))\n    device_active = in_claims or has_hb or has_sensor'
NEW = 'has_sensor  = bool(device_sensor_cache.get(did))\n    has_camera  = did.replace("lemari-","") in [str(k) for k in _cam_frames.keys()] or str(tetasco_id) in _cam_frames\n    device_active = in_claims or has_hb or has_sensor or has_camera'

if OLD in main_py:
    main_py = main_py.replace(OLD, NEW, 1)
    print('[OK] Camera frame check ditambahkan ke share-token')
elif 'has_camera' in main_py:
    print('[INFO] Camera check sudah ada')
else:
    print('[WARN] Tidak bisa patch inline, skip')

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()
print('[OK] main.py updated')

# 4. Rebuild dan restart
r('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -5', '4. Build backend', timeout=120)
r('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -8', '5. Docker up', timeout=30)
time.sleep(12)

r('curl -s http://localhost:8000/api/health', '6. Health check')
r('curl -s -X POST http://localhost:8000/api/tetasco/1/share-token -H "Content-Type: application/json" -d \'{"appId":"anyid"}\'',
  '7. Test share token (harus OK)')
r('docker ps --format "{{.Names}}\\t{{.Status}}"', '8. Container status')

sv.close()
print('\n✅ Done!')
