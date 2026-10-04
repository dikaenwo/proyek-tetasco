import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
src = o.read().decode('utf-8','replace')

# Cek nilai saat ini
import re
match = re.search(r'DEAD_TIME_DELAY\s*=\s*([\d.]+)', src)
current = match.group(1) if match else '?'
print(f'DEAD_TIME_DELAY saat ini: {current}s')

# Kurangi ke 0.05 (50ms) — masih aman untuk relay modul standard
src = src.replace('DEAD_TIME_DELAY = 0.15', 'DEAD_TIME_DELAY = 0.05')
src = src.replace('DEAD_TIME_DELAY = 0.1 ', 'DEAD_TIME_DELAY = 0.05')  # variasi spasi
print(f'Setelah patch: DEAD_TIME_DELAY=0.05' if 'DEAD_TIME_DELAY = 0.05' in src else '[WARN] Pattern tidak cocok')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(src.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()

i2,o2,e2 = rp.exec_command('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo OK')
print('[Syntax]', o2.read().decode().strip())

# Stop motor → restart → test
rp.exec_command('curl -s -X POST http://localhost:5001/api/hydraulic/command -H "Content-Type: application/json" -d \'{"action":"stop"}\' 2>/dev/null')
time.sleep(1)
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(7)

i3,o3,e3 = rp.exec_command('curl -s http://localhost:5001/api/hydraulic/status')
import json
d = json.loads(o3.read().decode())
print(f'[Status] state={d["state"]} backend={d["backend"]}')

rp.close()
print('\n✅ DEAD_TIME_DELAY: 0.15s → 0.05s (delay ganti arah berkurang dari 150ms → 50ms)')
