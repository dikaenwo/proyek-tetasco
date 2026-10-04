"""explore_lemari1_deep.py — Deep exploration app.py dan cloud_sync"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('tetasco1', 22, 'tetasco1', 'saumata1192', timeout=10)
print('Connected!', flush=True)

def r(cmd, lbl=''):
    if lbl: print(f'\n{"="*55}\n  {lbl}\n{"="*55}', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    print(out if out else '(empty)', flush=True)
    return out

r('cat ~/Penetas-Telur/backend/app.py', 'app.py FULL')
r('ls -la ~/Penetas-Telur/backend/hardware/', 'hardware/ contents')
r('cat ~/Penetas-Telur/backend/hardware/__init__.py 2>/dev/null', 'hardware/__init__.py')
r('cat ~/Penetas-Telur/backend/hardware/cloud_sync.py 2>/dev/null', 'cloud_sync.py')
r('ls ~/Penetas-Telur/backend/sensors/', 'sensors/ folder')
r('cat ~/Penetas-Telur/backend/sensors/__init__.py 2>/dev/null | head -30', 'sensors/__init__.py')
r('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py', 'hydraulic_controller.py')

c.close()
print('\nDone!', flush=True)
