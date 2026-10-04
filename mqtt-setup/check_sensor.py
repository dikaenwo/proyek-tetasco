"""check_sensor.py — Cek SensorManager lemari-1"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8','replace').strip()
    print(out[:6000] if out else '(empty)', flush=True)
    return out

r(f'cat {PROJ}/sensors/dht_sensor.py 2>/dev/null || cat {PROJ}/sensors/sht20_sensor.py 2>/dev/null | head -80', 'Sensor files')
r(f'grep -n "def \|class \|sensor_manager\|SensorManager" {PROJ}/app.py | head -30', 'SensorManager di app.py')
r(f'grep -n "class SensorManager\|def get\|def read\|def latest" {PROJ}/sensors/*.py 2>/dev/null | head -30', 'SensorManager methods')
r(f'cat {PROJ}/sensors/dht_sensor.py 2>/dev/null | head -60', 'dht_sensor.py')
r(f'grep -A5 "sensor_manager" {PROJ}/app.py | head -30', 'sensor_manager usage in app.py')

# Test baca sensor live
r(f'curl -s http://localhost:5001/api/sensor', 'Live sensor data')
c.close()
