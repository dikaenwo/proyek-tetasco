import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Baca cloud_sync.py
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py')
cs = o.read().decode('utf-8','replace')
print(f'cloud_sync.py: {len(cs)} chars')

if 'pending-commands' in cs:
    print('[INFO] pending-commands polling sudah ada')
else:
    # Cari method _sync_loop atau _worker untuk tambahkan polling
    r("grep -n 'def _sync\\|def _worker\\|def _run\\|def run\\|while.*_running\\|time.sleep' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -20", 'Loop structure')

r("grep -n -A 20 'def _sync_loop\\|def _worker\\|while self._running' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -40", 'Worker loop')
r("grep -n 'gpio_controller\\|set_actuator\\|lamp_1\\|fan\\|mist' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -15", 'Actuator control')

rp.close()
