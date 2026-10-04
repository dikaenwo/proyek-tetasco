"""
fix_403_and_queue.py
=====================
Root cause ditemukan:
1. Raspi → tetasco.my.id → Cloudflare 403 (blokir non-browser UA)
2. Fix: Raspi pakai IP LAN langsung 192.168.1.14:8000 (bypass Cloudflare)
3. Patch control endpoint line ~127 untuk juga update _cmd_queue
"""
import paramiko, sys, io, time, json
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
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras_bg(cmd):
    """Fire-and-forget background command."""
    transport = rp.get_transport()
    chan = transport.open_session()
    chan.exec_command(cmd)
    time.sleep(1)
    chan.close()

# ══════════════════════════════════════════════════════
# FIX 1: Update cloud_config.json pakai LAN IP
# ══════════════════════════════════════════════════════
print('\n=== FIX 1: Ganti cloud_base_url ke LAN IP ===')
cfg = {
    "cloud_base_url":       "http://192.168.1.14:8000",
    "tetasco_id":           1,
    "sync_interval_seconds": 5,
    "sync_devices_from_cloud": True
}
cfg_json = json.dumps(cfg, indent=2)
sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(cfg_json.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_config.json')
sftp.close()
print(f'[OK] cloud_config.json: {cfg_json}')

# Restart Raspi app.py
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo ok', 'Kill old process')
ras_bg('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Raspi app.py started')
time.sleep(8)
ras('pgrep -fa "python3 backend/app.py" | head -1', 'Process check')

# ══════════════════════════════════════════════════════
# FIX 2: Patch ORIGINAL control endpoint (line ~127)
# ══════════════════════════════════════════════════════
print('\n=== FIX 2: Patch control endpoint (ORIGINAL) ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Cari original return statement di control_device (sebelum emergency stop)
# Target: tambah queue SEBELUM return DeviceCommandResponse
TARGET = '    return DeviceCommandResponse(\n        success=True,\n        device_id=device_id,\n        actuator=actuator,'

if TARGET in main_py:
    # Sisipkan queue update sebelum return
    QUEUE_UPDATE = '''    # ── Queue untuk Raspi HTTP polling (fallback dari MQTT) ──
    if '_cmd_queue' in dir():
        try:
            _cmd_queue(tetasco_id).appendleft({"device": actuator, "action": action, "ts": int(__import__("time").time())})
            if tetasco_id not in _desired_state:
                _desired_state[tetasco_id] = {}
            _desired_state[tetasco_id][actuator] = state
        except Exception:
            pass
    '''
    main_py = main_py.replace(TARGET, QUEUE_UPDATE + TARGET, 1)
    print('[OK] Queue update disisipkan sebelum return DeviceCommandResponse')
else:
    # Coba pattern lain
    alt_target = 'message=f"{actuator.upper()} {\'ON\' if state else \'OFF\'} — perintah dikirim ke {device_id}",'
    if alt_target in main_py:
        print('[INFO] Coba alternatif pattern...')
    else:
        # Lihat exact context
        idx = main_py.find('DeviceCommandResponse')
        print(f'[DEBUG] DeviceCommandResponse at idx: {idx}')
        if idx > 0:
            print(main_py[max(0,idx-200):idx+100])

# Deploy ke server host dan container
sftp2 = sv.open_sftp()
sftp2.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp2.putfo(io.BytesIO(main_py.encode()), '/tmp/main_patched.py')
sftp2.close()
srv('docker cp /tmp/main_patched.py tetasco-backend:/app/main.py && echo ok', 'Deploy ke container')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# ══════════════════════════════════════════════════════
# VERIFIKASI
# ══════════════════════════════════════════════════════
print('\n=== VERIFIKASI ===')
print('Tunggu 15 detik untuk sensor push pertama...')
time.sleep(15)

sensor = srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor data')
if '"online":true' in sensor:
    print('✅ SENSOR REALTIME BERFUNGSI!')
else:
    print('❌ Sensor masih offline - cek Raspi log')
    ras('tail -20 /tmp/tetasco_backend.log 2>/dev/null', 'Raspi log')

# Test control
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
time.sleep(1)
q = srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands')
if '"fan"' in q or '"device"' in q:
    print('✅ CONTROL QUEUE BERFUNGSI!')
else:
    print('❌ Queue masih kosong')

sv.close()
rp.close()
print('\n✅ Done!')
