"""check_sensors_folder.py — Cek sensors/ folder dan SensorManager.read() return format"""
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

r(cl, f'ls {PROJ}/sensors/', '1. sensors/ folder')
r(cl, f'grep -n "class SensorManager\|def read\|active_sensor\|sensor_type\|is_hardware" {PROJ}/sensors/*.py | head -25',
  '2. SensorManager methods')
r(cl, f'grep -n "from sensors\|import.*sensor" {PROJ}/app.py | head -10', '3. Import di app.py')

# Test baca sensor langsung
r(cl, f'''timeout 15 python3 << 'PYEOF' 2>&1
import sys, os
sys.path.insert(0, "{PROJ}")
from sensors.sensor_manager import SensorManager, sensor_manager as sm
import inspect

# Cek signature
print("Signature read():", inspect.signature(sm.read))
print("Methods:", [m for m in dir(sm) if not m.startswith("_")])

# Baca sensor
result = sm.read(heater=False, fan=False, humidifier=False)
print("\\nResult from read():")
for k, v in result.items():
    print(f"  {k}: {v}")
PYEOF
''', '4. Test SensorManager.read() langsung')

cl.close()
print('\nDone!', flush=True)
