import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek apakah server masih punya DirectFwd
srv("docker exec tetasco-backend grep -n '_forward_to_raspi\\|DirectFwd' /app/main.py | head -10", 'DirectFwd di server')

# Pastikan main.py di container TIDAK ada DirectFwd di control endpoint
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

fwd_in_control = '_fwd = _forward_to_raspi' in main_py
print(f'[INFO] DirectFwd dalam control endpoint: {fwd_in_control}')

if fwd_in_control:
    print('[!] DirectFwd masih ada! Hapus sekarang...')
    fwd_idx = main_py.find('_fwd = _forward_to_raspi(tetasco_id')
    start = main_py.rfind('\n    # ──', 0, fwd_idx)
    end = main_py.find('\n    )', fwd_idx) + 6
    old_block = main_py[start:end]
    new_block = '''

    # ── MQTT primary (DirectFwd dihapus: hindari race condition) ──
    device_status_cache[device_id][actuator] = state
    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        actuator=actuator,
        state=state,
        mqtt_sent=mqtt_sent,
        message=f"{actuator.upper()} {'ON' if state else 'OFF'} — {'MQTT instant' if mqtt_sent else 'queued'}",
    )'''
    main_py = main_py[:start] + new_block + main_py[end:]
    print('[OK] DirectFwd dihapus')

    sftp = sv.open_sftp()
    sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
    sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_final.py')
    sftp.close()
    srv('docker cp /tmp/main_final.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
    srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
    time.sleep(12)
    srv('curl -s http://localhost:8000/api/health', 'Health')
    # Rebuild permanen
    srv('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -3', 'Rebuild', t=120)
    srv('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -2')
    time.sleep(8)
    srv('curl -s http://localhost:8000/api/health', 'Health final')
else:
    print('[OK] DirectFwd sudah tidak ada di control endpoint')
    srv('curl -s http://localhost:8000/api/health', 'Health')

# Final test: fan & humidifier ON→OFF cepat (300ms)
print('\n=== FINAL RACE TEST ===')
time.sleep(3)
results = []
for device in ['fan', 'humidifier']:
    # ON lalu OFF
    i1,o1,_ = sv.exec_command(f'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/{device}/on')
    time.sleep(0.3)
    i2,o2,_ = sv.exec_command(f'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/{device}/off')
    o1.read(); o2.read()
    time.sleep(1.5)
    i3,o3,_ = rp.exec_command(f"curl -s http://localhost:5001/api/actuators")
    data = o3.read().decode('utf-8','replace').strip()
    import json
    try:
        d = json.loads(data)
        name = 'mist_maker' if device == 'humidifier' else 'fan'
        state = d.get(name, '?')
        ok = state == False
        print(f'  {device}: final={state} {"✅ OFF (benar!)" if ok else "❌ masih ON!"}')
    except: print(f'  {device}: {data[:60]}')
    time.sleep(0.5)

rp.close()
sv.close()
print('\n✅ Final check selesai!')
