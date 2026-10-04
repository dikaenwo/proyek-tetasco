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

# Baca main.py dari container
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Cari blok _forward_to_raspi di control endpoint
fwd_idx = main_py.find('_fwd = _forward_to_raspi(tetasco_id')
if fwd_idx > 0:
    # Tampilkan konteks lengkap
    ctx = main_py[max(0,fwd_idx-50):fwd_idx+400]
    print('[DEBUG] Konteks DirectFwd block:')
    print(ctx)
    print('---')

    # Ganti seluruh blok _fwd dengan return langsung
    # Cari dari komentar sebelumnya sampai akhir return
    start = main_py.rfind('\n    # ──', 0, fwd_idx)
    end   = main_py.find('\n    )', fwd_idx) + 6  # akhir return statement
    
    old_block = main_py[start:end]
    print(f'\n[Blok yang akan diganti ({len(old_block)} chars)]:\n{old_block}\n---')
    
    new_block = '''

    # ── MQTT primary (DirectFwd dihapus untuk hindari race condition) ──
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
    print('[OK] DirectFwd dihapus dari control endpoint')
else:
    print('[ERR] _forward_to_raspi tidak ditemukan!')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_mqtt_only.py')
sftp.close()
srv('docker cp /tmp/main_mqtt_only.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Test race: ON → OFF cepat (harus akhir OFF)
print('\n=== Test race: humidifier ON → OFF (300ms gap) ===')
time.sleep(2)
i2,o2,e2 = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/on')
time.sleep(0.3)
i3,o3,e3 = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/off')
o2.read(); o3.read()  # consume

time.sleep(1.5)
ras('tail -6 /tmp/tetasco_backend.log | grep -i "INSTANT\\|GPIO"', 'Raspi final state (harus OFF terakhir)')

# Test balik: OFF → ON
print('\n=== Test race: humidifier OFF → ON (300ms gap) ===')
i4,o4,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/off')
time.sleep(0.3)
i5,o5,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/on')
o4.read(); o5.read()

time.sleep(1.5)
ras('tail -4 /tmp/tetasco_backend.log | grep -i "INSTANT\\|GPIO"', 'Raspi final state (harus ON terakhir)')

rp.close()
sv.close()
print('\n✅ Done!')
