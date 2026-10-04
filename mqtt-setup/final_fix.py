"""
final_fix.py
=============
1. Patch server: modifikasi EXISTING control endpoint untuk juga simpan ke _command_queues
2. Restart Raspi app.py dengan cara yang benar
3. Verifikasi end-to-end
"""
import paramiko, sys, io, time, re
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

def ras(cmd, lbl='', t=15):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# ══════════════════════════════════════════════════════
# RASPI: Start properly
# ══════════════════════════════════════════════════════
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 2; echo ok', 'Kill old')
ras('setsid bash -c "cd /home/tetasco1/Penetas-Telur && python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1" &', 'Start dengan setsid')
time.sleep(8)
ras('pgrep -fa "python3 backend/app.py" | head -2', 'Check process')
ras('tail -8 /tmp/tetasco_backend.log', 'Log tail')

# ══════════════════════════════════════════════════════
# SERVER: Patch existing control endpoint
# ══════════════════════════════════════════════════════
print('\n=== PATCH SERVER ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'Container main.py: {len(main_py)} chars')

# Cari existing control endpoint handler yang pakai MQTT
# Tambahkan _command_queues update setelah line "mqtt_sent = True" atau setelah asyncio
if '_cmd_queue(tetasco_id)' not in main_py:
    # Cari function handle_device_control atau similar
    # Dari response {"mqtt_sent":true} kita tau ada mqtt publish
    # Tambahkan queue update setelah mqtt publish logic
    
    # Pattern: setelah "mqtt_sent = True" tambahkan queue
    patterns = [
        ('mqtt_sent = True', 'mqtt_sent = True\n    # Queue for Raspi HTTP polling fallback\n    _cmd_queue(tetasco_id).appendleft({"device": device_name, "action": action, "ts": int(_relay_time.time())})\n    _desired_state[tetasco_id] = _desired_state.get(tetasco_id, {})\n    _desired_state[tetasco_id][_DEV_MAP.get(device_name, device_name)] = (action == "on")'),
        ('"mqtt_sent": True', '"mqtt_sent": True,\n        "queued": _cmd_queue(tetasco_id).appendleft({"device": device_name, "action": action, "ts": int(_relay_time.time())}) or True'),
    ]
    
    patched = False
    for old, new in patterns:
        if old in main_py:
            main_py = main_py.replace(old, new, 1)
            patched = True
            print(f'[OK] Patched: {old[:30]}...')
            break
    
    if not patched:
        # Cari endpoint yang return mqtt_sent
        idx = main_py.find('"mqtt_sent"')
        if idx > 0:
            ctx = main_py[max(0,idx-500):idx+200]
            print('[DEBUG] Context sekitar mqtt_sent:')
            print(ctx[:400])
        else:
            print('[WARN] Pattern tidak ditemukan')
else:
    print('[INFO] _cmd_queue sudah ada di container main.py')

# Deploy patched version
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_final.py')
sftp.close()
srv('docker cp /tmp/main_final.py tetasco-backend:/app/main.py && echo ok', 'Deploy ke container')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)

srv('curl -s http://localhost:8000/api/health', 'Health check')

# ══════════════════════════════════════════════════════
# VERIFIKASI END-TO-END
# ══════════════════════════════════════════════════════
print('\n=== VERIFIKASI ===')
time.sleep(5)

# Sensor (Raspi sudah jalan 20+ detik)
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor (harus online=true)')

# Control test
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON command')
time.sleep(1)
result = srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands (harus ada fan)')
if '"fan"' in result:
    print('✅ Queue berfungsi!')
else:
    print('❌ Queue masih kosong - cek server logs')
    srv('docker logs tetasco-backend --tail 20 2>&1', 'Server logs')

# Raspi log: apakah cloud_sync berjalan?
time.sleep(5)
ras('tail -15 /tmp/tetasco_backend.log', 'Raspi log terbaru')

sv.close()
rp.close()
print('\n✅ Done!')
