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

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Patch cloud_sync: disable poll_and_execute_commands
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cloud_sync = o.read().decode('utf-8','replace')

OLD_POLL_CALL = '''            # Poll pending commands dari HP (fast control)
            self.poll_and_execute_commands()'''

NEW_POLL_CALL = '''            # Poll pending commands DISABLED — MQTT handles instant delivery
            # self.poll_and_execute_commands()  # disabled: race condition'''

if OLD_POLL_CALL in cloud_sync:
    cloud_sync = cloud_sync.replace(OLD_POLL_CALL, NEW_POLL_CALL, 1)
    print('[OK] poll_and_execute_commands disabled di cloud_sync!')
else:
    print('[WARN] Pattern tidak ditemukan!')
    ras("grep -n 'poll_and_execute' ~/Penetas-Telur/backend/hardware/cloud_sync.py", 'poll calls')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(cloud_sync.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/cloud_sync.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/cloud_sync.py && echo OK', 'Syntax OK')

# Restart Raspi
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
transport = rp.get_transport()
chan = transport.open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && > /tmp/tetasco_backend.log && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1)
chan.close()
time.sleep(10)

ras('ss -tnp | grep 1883 | head -1', 'MQTT connected')
ras('grep -i mqtt /tmp/tetasco_backend.log | head -5', 'MQTT log')

# Test race: toggle cepat ON→OFF 3x
print('\n=== Race test: ON→OFF cepat (300ms) ===')
time.sleep(3)
for trial in range(3):
    # Kirim ON lalu OFF
    i1,o1,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/on')
    time.sleep(0.3)
    i2,o2,_ = sv.exec_command('curl -s -X POST http://localhost:8000/api/tetasco/1/devices/humidifier/off')
    o1.read(); o2.read()
    time.sleep(1.5)
    # Cek state akhir
    i3,o3,_ = rp.exec_command('curl -s http://localhost:5001/api/actuators | python3 -c "import sys,json;d=json.load(sys.stdin);print(\'humidifier:\',d.get(\'humidifier\',\'?\'),\'mist_maker:\',d.get(\'mist_maker\',\'?\'))"')
    state = o3.read().decode('utf-8','replace').strip()
    ok = 'False' in state or 'false' in state.lower() or 'off' in state.lower()
    print(f'  Trial {trial+1}: {state} {"✅ OFF" if ok else "❌ MASIH ON"}')
    time.sleep(0.5)

# Rebuild server permanen
print('\n=== Rebuild server ===')
srv('cd ~/tetasco-connect && docker compose build backend 2>&1 | tail -3', t=120)
srv('cd ~/tetasco-connect && docker compose up -d 2>&1 | tail -2')
time.sleep(8)
srv('curl -s http://localhost:8000/api/health', 'Health')

rp.close()
sv.close()
print('\n✅ Done! Ghost toggle fix selesai & server rebuilt!')
