"""read_key_files.py — Baca app.py dan cloud_sync.py"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('tetasco1', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl=''):
    if lbl: print(f'\n{"="*55}\n  {lbl}\n{"="*55}', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    print(out[:8000] if out else '(empty)', flush=True)
    return out

r('wc -l ~/Penetas-Telur/backend/app.py', 'app.py line count')
r('head -120 ~/Penetas-Telur/backend/app.py', 'app.py TOP (import & config)')
r('grep -n "cloud_sync\|CloudSync\|import\|from " ~/Penetas-Telur/backend/app.py | head -40', 'app.py imports & cloud_sync refs')
r('ls -la ~/Penetas-Telur/backend/hardware/', 'hardware/ list')
r('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py 2>/dev/null | head -100', 'cloud_sync.py TOP')
r('grep -n "def \|class \|mqtt\|MQTT\|websocket\|http\|request" ~/Penetas-Telur/backend/hardware/cloud_sync.py 2>/dev/null | head -40', 'cloud_sync methods & protocols')
r('ls ~/Penetas-Telur/backend/sensors/', 'sensors/ list')
r('head -50 ~/Penetas-Telur/backend/sensors/sensor_manager.py 2>/dev/null || head -50 ~/Penetas-Telur/backend/sensors/__init__.py 2>/dev/null', 'sensor_manager top')
r('grep -rn "tetasco_id\|device_id\|DEVICE_ID\|lemari" ~/Penetas-Telur/backend/ 2>/dev/null | head -20', 'Device ID config')
r('cat ~/Penetas-Telur/backend/hardware/config.json 2>/dev/null || find ~/Penetas-Telur -name "*.json" -not -path "*/node_modules/*" | head -10', 'config files')

c.close()
print('\nDone!', flush=True)
