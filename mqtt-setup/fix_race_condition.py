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

# === PATCH SERVER: MQTT primary, DirectFwd hanya fallback ===
print('=== PATCH SERVER: MQTT primary, DirectFwd fallback ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Ganti logika control: MQTT dulu, DirectFwd hanya jika MQTT gagal
OLD_CONTROL = '''    # ── Direct forward ke Raspi via LAN (instant!) ──
    _fwd = _forward_to_raspi(tetasco_id, actuator, state)
    if _fwd.get("ok") and _fwd.get("raspi"):
        device_status_cache[device_id][actuator] = _fwd["raspi"].get("state", state)
    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        actuator=actuator,
        state=state,
        mqtt_sent=_fwd.get("ok", mqtt_sent),
        message=f"{actuator.upper()} {'ON' if state else 'OFF'} \u2014 {'GPIO OK' if _fwd.get('ok') else 'queued'}",
    )'''

NEW_CONTROL = '''    # ── Kontrol: MQTT primary → DirectFwd fallback jika MQTT gagal ──
    if mqtt_sent:
        # MQTT berhasil publish → Raspi subscriber akan eksekusi
        # Update cache saja, JANGAN DirectFwd (hindari race condition)
        device_status_cache[device_id][actuator] = state
        return DeviceCommandResponse(
            success=True, device_id=device_id, actuator=actuator,
            state=state, mqtt_sent=True,
            message=f"{actuator.upper()} {'ON' if state else 'OFF'} \u2014 MQTT instant",
        )
    else:
        # MQTT gagal → gunakan DirectFwd sebagai fallback
        _fwd = _forward_to_raspi(tetasco_id, actuator, state)
        if _fwd.get("ok") and _fwd.get("raspi"):
            device_status_cache[device_id][actuator] = _fwd["raspi"].get("state", state)
        return DeviceCommandResponse(
            success=True, device_id=device_id, actuator=actuator,
            state=state, mqtt_sent=False,
            message=f"{actuator.upper()} {'ON' if state else 'OFF'} \u2014 {'DirectFwd OK' if _fwd.get('ok') else 'queued'}",
        )'''

if OLD_CONTROL in main_py:
    main_py = main_py.replace(OLD_CONTROL, NEW_CONTROL, 1)
    print('[OK] Server: MQTT primary, DirectFwd fallback')
else:
    print('[WARN] Pattern tidak cocok, cari alternatif...')
    idx = main_py.find('return DeviceCommandResponse(')
    print(main_py[max(0,idx-300):idx+200])

# === PATCH RASPI: Nonaktifkan pending-commands polling (gunakan MQTT saja) ===
print('\n=== PATCH RASPI: Disable pending-commands polling ===')
i2,o2,e2 = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cloud_sync = o2.read().decode('utf-8','replace')
ras("grep -n 'pending.command\\|poll_command\\|CloudCtrl\\|sync_from_cloud' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -10", 'Pending commands code')

# Cek nama method polling pending-commands
if 'sync_devices_from_cloud' in cloud_sync or 'pending' in cloud_sync.lower():
    # Set sync_devices_from_cloud = False agar tidak polling
    old_cfg_check = '"sync_devices_from_cloud": True'
    print(f'sync_devices_from_cloud found: {old_cfg_check in cloud_sync}')

# Update cloud_config.json: matikan sync_devices_from_cloud
import json
cfg = {
    "cloud_base_url": "http://192.168.1.14:8000",
    "tetasco_id": 1,
    "sync_interval_seconds": 5,
    "sync_devices_from_cloud": False   # ← MQTT yang handle sekarang, polling dimatikan
}
sftp_r = rp.open_sftp()
sftp_r.putfo(io.BytesIO(json.dumps(cfg, indent=2).encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_config.json')
sftp_r.close()
print('[OK] sync_devices_from_cloud=False (polling dimatikan, MQTT takes over)')

# Deploy server fix
sftp_s = sv.open_sftp()
sftp_s.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp_s.putfo(io.BytesIO(main_py.encode()), '/tmp/main_mqtt_primary.py')
sftp_s.close()
srv('docker cp /tmp/main_mqtt_primary.py tetasco-backend:/app/main.py && echo ok', 'Deploy server')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# Restart Raspi dengan config baru
rp.exec_command('kill -9 966536 2>/dev/null; pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
print('[OK] Raspi restart dengan polling dimatikan')
time.sleep(10)

ras('ss -tnp | grep 1883 | head -2', 'MQTT connected')
ras('tail -5 /tmp/tetasco_backend.log | grep -v GET', 'Raspi log')

# Test race condition: ON lalu langsung OFF
print('\n=== Test race: ON → OFF cepat ===')
time.sleep(3)
import threading

def send(action):
    i,o,e = sv.exec_command(f'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/{action}')
    print(f'  {action}: {o.read().decode()[:50]}')

send('on')
time.sleep(0.3)  # 300ms kemudian OFF
send('off')
time.sleep(2)
ras('tail -6 /tmp/tetasco_backend.log | grep -i "mqtt\\|GPIO\\|INSTANT"', 'Raspi final state (harus OFF)')

rp.close()
sv.close()
print('\n✅ Fix race condition selesai!')
