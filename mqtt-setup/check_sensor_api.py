"""check_sensor_api.py — Cek signature SensorManager.read() dan field yang dikembalikan"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Cek signature SensorManager.read()
r(cl, f'grep -n "def read\|def get_latest\|def get_reading\|active_sensor" {PROJ}/hardware/sensor_manager.py | head -20',
  '1. SensorManager methods')

# 2. Cek apa yang dikembalikan read()
r(cl, f'''timeout 10 python3 << 'PYEOF' 2>&1
import sys
sys.path.insert(0, "{PROJ}")
from hardware.sensor_manager import SensorManager

sm = SensorManager()
import inspect
sig = inspect.signature(sm.read)
print("Signature read():", sig)
result = sm.read(False, False, False)
print("Result keys:", list(result.keys()) if result else "None")
print("Full result:", result)
PYEOF
''', '2. Test SensorManager.read(False,False,False)')

# 3. Cek field active_sensor_type
r(cl, f'grep -n "active_sensor_type\|sensor_type\|sensor_name" {PROJ}/hardware/sensor_manager.py | head -10',
  '3. Sensor type field di SensorManager')

cl.close()
print('\nDone!', flush=True)
