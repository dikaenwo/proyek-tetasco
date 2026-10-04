import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip())

# Lihat apa yang dikirim ke sensors/history
r("grep -n 'sensors/history\\|sensor_data\\|push_data\\|POST\\|sync_sensor\\|_push' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -20", 'cloud_sync sensors/history usage')
r("grep -n -A 15 'sensors/history' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -40", 'sensors/history POST detail')
r("grep -n -A 10 'push_device_state\\|push_data' ~/Penetas-Telur/backend/hardware/cloud_sync.py | head -30", 'push_device_state detail')
r("cat ~/Penetas-Telur/backend/hardware/cloud_sync.py | grep -A 20 'def _sync_sensor\\|def sync_sensor\\|def _push_sensor'", 'sync sensor method')

rp.close()
