import paramiko, sys, io, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca file
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
ctrl = o.read().decode('utf-8','replace')

# Cari signature yang ada
import re
m = re.search(r'def start_timed_oscillation\([^)]+\)', ctrl, re.DOTALL)
if m:
    print('[FOUND] Signature saat ini:')
    print(m.group())

# Ganti signature apapun yang ada dengan yang baru
ctrl = re.sub(
    r'def start_timed_oscillation\(([^)]+)\)',
    lambda _: (
        'def start_timed_oscillation(\n'
        '        self,\n'
        '        n_cycles: int = 3,\n'
        '        t_center_to_edge: float = 3.0,\n'
        '        t_full: float = 8.3,\n'
        '        t_up: float = None,\n'
        '        t_down: float = None,\n'
        '    )'
    ),
    ctrl,
    count=1,
    flags=re.DOTALL
)
print('[OK] Signature diperbarui')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(ctrl.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo OK', 'Syntax')

# Restart
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Restart')
time.sleep(7)

# Test t_up / t_down
i2,o2,e2 = rp.exec_command('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d \'{"t_down":7.0,"t_up":8.0,"n_cycles":1,"t_center_to_edge":2.8}\'')
raw = o2.read().decode('utf-8','replace').strip()
try:
    d = json.loads(raw)
    print(f'[TEST] t_down={d["t_down"]} t_up={d["t_up"]} total={d["total_duration_sec"]}s state={d["state"]}')
except:
    print('[RAW]', raw[:200])

rp.close()
print('\n✅ Selesai! Refresh halaman kalibrasi di browser.')
