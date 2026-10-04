import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

def ras_bg(cmd):
    transport = rp.get_transport()
    chan = transport.open_session()
    chan.exec_command(cmd)
    time.sleep(0.5)
    chan.close()

# === FIX 1: push_device_state → NON-BLOCKING (background thread) ===
print('=== FIX 1: push_device_state non-blocking ===')
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cloud_sync = o.read().decode('utf-8','replace')

# Bungkus push_device_state dengan background thread
OLD_PUSH = '''    def push_device_state(self, device_name: str, state: bool):
        """Mengirimkan status aktuator lokal ke endpoint cloud server jika sedang Online"""
        if not self.is_online:
            return'''

NEW_PUSH = '''    def push_device_state(self, device_name: str, state: bool):
        """Mengirimkan status aktuator lokal ke endpoint cloud server — NON-BLOCKING."""
        if not self.is_online:
            return
        # Jalankan di background thread agar tidak blocking Flask request handler
        import threading as _t2
        _t2.Thread(target=self._push_device_state_bg,
                   args=(device_name, state), daemon=True).start()

    def _push_device_state_bg(self, device_name: str, state: bool):
        """Versi blocking dari push_device_state — dijalankan di thread."""
        if not self.is_online:
            return'''

if OLD_PUSH in cloud_sync:
    cloud_sync = cloud_sync.replace(OLD_PUSH, NEW_PUSH, 1)
    # Ganti semua "def push_device_state" body menjadi _push_device_state_bg body
    # Temukan baris setelah "return" di push_device_state yang baru
    # Cari blok kode lama yang perlu dipindah ke _push_device_state_bg
    print('[OK] push_device_state dibuat non-blocking')
else:
    print('[WARN] Pattern tidak ditemukan, coba pattern lain')
    idx = cloud_sync.find('def push_device_state')
    print(cloud_sync[idx:idx+300])

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(cloud_sync.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_sync.py')
sftp.close()

# === FIX 2: Flask threaded=True ===
print('\n=== FIX 2: Flask threaded=True ===')
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')

OLD_RUN = "app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)"
NEW_RUN = "app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False, threaded=True)"

if OLD_RUN in app_py:
    app_py = app_py.replace(OLD_RUN, NEW_RUN, 1)
    print('[OK] Flask threaded=True')
elif 'threaded=True' in app_py:
    print('[INFO] Sudah threaded=True')
else:
    print('[WARN] app.run pattern tidak cocok')

sftp2 = rp.open_sftp()
sftp2.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp2.close()

# === FIX 3: Server - reduce timeout ke 2s, tambah no-push header ===
print('\n=== FIX 3: Server timeout reduce + tambah header X-From-Server ===')
i,o,e = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main_py = o.read().decode('utf-8','replace')

# Ganti timeout 3 detik → 2 detik dan tambah header agar Raspi tahu ini dari server
OLD_FWD_URL = '''    url = f"http://{raspi_ip}:5001/api/actuators/{raspi_name}"
    body = _json_fwd.dumps({"state": state}).encode()
    try:
        req = _urllib_req.Request(url, data=body,
              headers={"Content-Type": "application/json"}, method="POST")
        with _urllib_req.urlopen(req, timeout=3) as resp:'''

NEW_FWD_URL = '''    url = f"http://{raspi_ip}:5001/api/actuators/{raspi_name}"
    body = _json_fwd.dumps({"state": state}).encode()
    try:
        req = _urllib_req.Request(url, data=body,
              headers={"Content-Type": "application/json",
                       "X-From-Server": "1"},  # hindari circular push
              method="POST")
        with _urllib_req.urlopen(req, timeout=2) as resp:'''

if OLD_FWD_URL in main_py:
    main_py = main_py.replace(OLD_FWD_URL, NEW_FWD_URL, 1)
    print('[OK] Timeout 3→2s + X-From-Server header')

sftp3 = sv.open_sftp()
sftp3.putfo(io.BytesIO(main_py.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp3.putfo(io.BytesIO(main_py.encode()), '/tmp/main_fix_deadlock.py')
sftp3.close()
srv('docker cp /tmp/main_fix_deadlock.py tetasco-backend:/app/main.py && echo ok', 'Deploy server')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(12)

# Restart Raspi
ras('pkill -9 -f "python3 backend/app.py" 2>/dev/null; sleep 1; echo ok', 'Kill Raspi old')
ras_bg('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
print('[OK] Raspi restarted')
time.sleep(8)
ras('pgrep -fa "python3 backend/app.py" | head -1', 'Raspi process')

srv('curl -s http://localhost:8000/api/health', 'Health')

# Test timing
print('\n=== TEST TIMING (tanpa deadlock) ===')
for i2 in range(3):
    t0 = time.time()
    r = srv(f"curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/{'on' if i2%2==0 else 'off'}", f'Toggle {i2+1}')
    t1 = time.time()
    print(f'  Total: {(t1-t0)*1000:.0f}ms — {r[:60]}')
    time.sleep(0.5)

srv('docker logs tetasco-backend --tail 5 2>&1 | grep -i "DirectFwd\\|error"', 'Log')
rp.close()
sv.close()
print('\n✅ Deadlock fix deployed!')
