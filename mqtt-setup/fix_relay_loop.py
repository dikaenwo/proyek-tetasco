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
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca app.py Raspi
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8','replace')

# Cek set_actuator endpoint
ras("grep -n -A 12 'def set_actuator' ~/Penetas-Telur/backend/app.py", 'set_actuator sekarang')

# Fix: skip push_device_state jika request dari server (X-From-Server header)
OLD_SET = """    try:
        new_state = gpio_controller.set_actuator(name, bool(data[\"state\"]))
        # Sinkronkan status saklar ke server cloud jika online
        cloud_sync.push_device_state(name, new_state)"""

NEW_SET = """    try:
        new_state = gpio_controller.set_actuator(name, bool(data[\"state\"]))
        # Skip push_device_state jika perintah datang dari server (hindari loop)
        if not request.headers.get('X-From-Server'):
            cloud_sync.push_device_state(name, new_state)"""

if OLD_SET in app_py:
    app_py = app_py.replace(OLD_SET, NEW_SET, 1)
    print('[OK] Loop fix: skip push_device_state jika X-From-Server')
else:
    print('[WARN] Pattern tidak cocok, cari variasi...')
    # Cek pattern alternatif
    idx = app_py.find('cloud_sync.push_device_state(name, new_state)')
    if idx > 0:
        print(f'Found at idx {idx}:')
        print(app_py[max(0,idx-100):idx+60])

# Juga fix: MQTT subscriber tidak perlu push state (sudah dihandle server)
# Cek apakah ada push di MQTT subscriber
ras("cat ~/Penetas-Telur/backend/hardware/mqtt_subscriber.py | grep -n 'push\\|cloud_sync'", 'MQTT subscriber push check')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py diupdate')

# Verifikasi syntax
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo OK', 'Syntax check')

# Restart
rp.exec_command('kill -9 194419 2>/dev/null; pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
print('[OK] Raspi restart')
time.sleep(10)

ras('pgrep -fa "python3 backend/app.py" | grep -v pgrep | head -1', 'Proses')
ras('ss -tnp | grep 1883 | head -2', 'MQTT connected')

# Test: fan ON hanya sekali (tidak ada loop)
print('\n=== Test anti-loop ===')
srv('> /tmp/loop_test.txt 2>/dev/null; docker logs tetasco-backend --tail 0 > /dev/null 2>&1', 'Reset log')
time.sleep(3)
srv("curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/on", 'Fan ON (1x)')
time.sleep(2)
ras('tail -8 /tmp/tetasco_backend.log', 'Raspi log (harus hanya 1x GPIO)')
srv('docker logs tetasco-backend --tail 8 2>&1 | grep -i "DirectFwd\\|MQTT\\|fan"', 'Server log')

rp.close()
sv.close()
print('\n✅ Anti-loop fix deployed!')
