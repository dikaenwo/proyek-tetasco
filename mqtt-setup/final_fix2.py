"""
final_fix2.py — perbaikan startup Raspi + server queue patch
"""
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
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras_bg(cmd):
    """Jalankan command di background tanpa blok channel."""
    transport = rp.get_transport()
    chan = transport.open_session()
    chan.exec_command(cmd)
    # Tidak read output — langsung close
    time.sleep(1)
    chan.close()

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# ══════════════════════════════════════════════════════
# 1. Restart Raspi app.py (non-blocking)
# ══════════════════════════════════════════════════════
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo ok', 'Kill old process')

# Jalankan background tanpa blok
ras_bg('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Raspi app.py started in background')
time.sleep(8)

ras('pgrep -fa "python3 backend/app.py" | head -2', 'Process running?')
ras('tail -10 /tmp/tetasco_backend.log 2>/dev/null', 'Log 10 baris terakhir')

# ══════════════════════════════════════════════════════
# 2. Patch server: tambah _cmd_queue ke existing endpoint
# ══════════════════════════════════════════════════════
print('\n=== PATCH SERVER CONTROL ENDPOINT ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'Container main.py: {len(main_py)} chars')

# Cari context di sekitar mqtt_sent untuk debug
idx = main_py.find('"mqtt_sent"')
if idx > 0:
    ctx = main_py[max(0,idx-300):idx+100]
    print('[DEBUG] Context mqtt_sent:')
    print(ctx)

if '_cmd_queue(tetasco_id)' not in main_py:
    # Patch: setelah set state di actuator endpoint, tambah queue
    # Cari pola return response yang berisi mqtt_sent
    old_return = '"mqtt_sent": True,'
    new_return  = '"mqtt_sent": True,\n        "queued": True,'
    
    if old_return in main_py:
        # Temukan fungsi di sekitar ini dan tambah queue update SEBELUM return
        # Cari index return statement yang berisi mqtt_sent
        ret_idx = main_py.rfind('return {', 0, main_py.find(old_return))
        # Sisipkan queue update sebelum return
        queue_code = '''    # Queue command untuk Raspi HTTP polling
    _cmd_queue(tetasco_id).appendleft({"device": device_name, "action": action, "ts": int(__import__("time").time())})
    _desired_state[tetasco_id] = _desired_state.get(tetasco_id, {})
    _desired_state[tetasco_id][_DEV_MAP.get(device_name, device_name)] = (action == "on")
    '''
        main_py = main_py[:ret_idx] + queue_code + main_py[ret_idx:]
        main_py = main_py.replace(old_return, new_return, 1)
        print('[OK] Queue update ditambahkan ke control endpoint')
    else:
        # Alternatif: ganti seluruh return block
        print('[WARN] Pattern return tidak ditemukan')
        # Print 500 chars sekitar mqtt_sent
        print(main_py[max(0,idx-100):idx+300])
else:
    print('[INFO] _cmd_queue sudah ada')

# Deploy
sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_q.py')
sftp.close()
srv('docker cp /tmp/main_q.py tetasco-backend:/app/main.py && echo ok', 'Deploy ke container')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)
srv('curl -s http://localhost:8000/api/health', 'Health')

# ══════════════════════════════════════════════════════
# 3. Verifikasi sensor + control
# ══════════════════════════════════════════════════════
print('\n=== VERIFIKASI END-TO-END ===')

# Sensor (Raspi sudah jalan 30+ detik — push interval 5 detik)
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor data')

# Control queue
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
time.sleep(1)
q_result = srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands')
if '"fan"' in q_result:
    print('✅ Control queue BERFUNGSI!')
else:
    print('❌ Queue masih kosong')

# Raspi log terbaru
time.sleep(5)
ras('tail -15 /tmp/tetasco_backend.log 2>/dev/null', 'Raspi log final')

sv.close()
rp.close()
print('\n✅ Done!')
