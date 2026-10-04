import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Baca main.py dari container
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
lines = main_py.split('\n')

# Tampilkan baris sekitar control_device (line 127)
print('[Lines 120-175 control_device original]:')
for i2, l in enumerate(lines[119:175], 120):
    print(f'{i2}: {l}')

# Temukan dan hapus duplikat fungsi ke-2 (async def control_device)
# Kemudian rename jadi _control_device_v2 agar tidak konflik
# Juga fix return DeviceCommandResponse jika ada masalah

# Cari posisi kedua def control_device
pos1 = main_py.find('\ndef control_device(')
pos2 = main_py.find('\nasync def control_device(')
print(f'\npos1={pos1}, pos2={pos2}')

if pos2 > 0:
    # Ganti "async def control_device" ke "async def _control_device_v2"
    main_py = main_py.replace(
        '\nasync def control_device(tetasco_id: int, device_name: str, action: str):',
        '\nasync def _control_device_queue_only(tetasco_id: int, device_name: str, action: str):',
        1
    )
    print('[OK] Duplikat fungsi direname ke _control_device_queue_only')

# Verifikasi jumlah def control_device sekarang
count_after = main_py.count('def control_device')
print(f'Jumlah def control_device setelah fix: {count_after}')

# Tampilkan baris 120-175 setelah fix
lines2 = main_py.split('\n')
print('\n[Lines 120-175 setelah fix]:')
for i2, l in enumerate(lines2[119:175], 120):
    print(f'{i2}: {l}')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_v4.py')
sftp.close()
srv('docker cp /tmp/main_v4.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')
result = srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON test')
if '"success"' in result:
    print('\n✅ CONTROL BERFUNGSI!')
else:
    srv('docker logs tetasco-backend --tail 15 2>&1', 'Error log')

time.sleep(1)
srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands')

sv.close()
