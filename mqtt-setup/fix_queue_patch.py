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

# Cek error dari server log
srv('docker logs tetasco-backend --tail 25 2>&1', 'Server error log')

# Baca main.py dari container, fix queue update
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')
print(f'\nContainer main.py: {len(main_py)} chars')

# Ganti kode queue yang error (pakai dir() check) dengan versi simple
OLD_QUEUE = '''    # ── Queue untuk Raspi HTTP polling (fallback dari MQTT) ──
    if '_cmd_queue' in dir():
        try:
            _cmd_queue(tetasco_id).appendleft({"device": actuator, "action": action, "ts": int(__import__("time").time())})
            if tetasco_id not in _desired_state:
                _desired_state[tetasco_id] = {}
            _desired_state[tetasco_id][actuator] = state
        except Exception:
            pass
    '''

NEW_QUEUE = '''    # ── Queue untuk Raspi HTTP polling ──
    try:
        _cmd_queue(tetasco_id).appendleft({"device": actuator, "action": action, "ts": int(_relay_time.time())})
        if tetasco_id not in _desired_state:
            _desired_state[tetasco_id] = {}
        _desired_state[tetasco_id][actuator] = state
    except Exception as _qe:
        pass
    '''

if OLD_QUEUE in main_py:
    main_py = main_py.replace(OLD_QUEUE, NEW_QUEUE, 1)
    print('[OK] Queue patch fixed (hapus dir() check)')
elif NEW_QUEUE in main_py:
    print('[INFO] Sudah terfix')
else:
    # Cari dan tampilkan konteks sekitar queue patch
    idx = main_py.find('_cmd_queue')
    if idx >= 0:
        print('[DEBUG] Context _cmd_queue:')
        print(main_py[max(0,idx-100):idx+200])

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.putfo(io.BytesIO(main_py.encode()), '/tmp/main_fix3.py')
sftp.close()
srv('docker cp /tmp/main_fix3.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(10)

srv('curl -s http://localhost:8000/api/health', 'Health')
srv('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor (harus masih online)')
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON')
time.sleep(1)
q = srv('curl -s http://localhost:8000/api/tetasco/1/pending-commands', 'Pending commands')
if '"fan"' in q or '"device"' in q:
    print('\n✅ CONTROL QUEUE BERFUNGSI!')
else:
    print('\n❌ Masih kosong — cek log')
    srv('docker logs tetasco-backend --tail 15 2>&1', 'Error log')

sv.close()
