import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca main.py
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Hapus baris yang salah
BAD_LINE = '''    if mqtt_sent:
        # Clear pending-commands queue (MQTT sudah deliver, tidak perlu polling)
        _cmd_queue[device_id] = {}'''

if BAD_LINE in main_py:
    main_py = main_py.replace(BAD_LINE, '', 1)
    print('[OK] Baris _cmd_queue[device_id] = {} dihapus!')
else:
    # Cari variasi
    idx = main_py.find('_cmd_queue[device_id]')
    if idx > 0:
        print(f'[Found] Context:\n{main_py[max(0,idx-100):idx+80]}')
        # Hapus baris itu
        lines = main_py.split('\n')
        lines = [l for l in lines if '_cmd_queue[device_id]' not in l]
        main_py = '\n'.join(lines)
        print('[OK] Baris dihapus via line filter')
    else:
        print('[WARN] Tidak ditemukan')

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_fix500.py')
sftp.close()

srv('docker cp /tmp/main_fix500.py tetasco-backend:/app/main.py && echo ok', 'Deploy fix')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)

# Verifikasi
srv("curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'HTTP status (harus 200)')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on 2>&1 | head -c 150", 'Response')

# Rebuild permanen
srv('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -3', 'Rebuild', t=120)
srv('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -2')
time.sleep(8)
srv('curl -s http://localhost:8000/api/health', 'Health final')

sv.close()
print('\n✅ Fix 500 error selesai!')
