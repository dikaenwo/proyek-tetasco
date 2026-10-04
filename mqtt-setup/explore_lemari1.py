"""explore_lemari1.py — Jelajahi struktur proyek Raspi Lemari 1"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('tetasco1', 22, 'tetasco1', 'saumata1192', timeout=10)
print('Connected to tetasco1!', flush=True)

def r(cmd, lbl=''):
    if lbl: print(f'\n{"="*55}\n  {lbl}\n{"="*55}', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    err = e.read().decode('utf-8', 'replace').strip()
    print(out if out else '(empty)', flush=True)
    if err and 'warning' not in err.lower(): print(f'ERR: {err[:300]}', flush=True)
    return out

r('uname -a && python3 --version', 'System info')
r('find ~/Penetas-Telur -type f -name "*.py" | sort', 'All Python files')
r('ls -la ~/Penetas-Telur/', 'Root project')
r('ls -la ~/Penetas-Telur/backend/', 'Backend folder')
r('ls -la ~/Penetas-Telur/backend/hardware/', 'Hardware folder')
r('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py', 'hydraulic_controller.py')
r('cat ~/Penetas-Telur/backend/main.py 2>/dev/null || cat ~/Penetas-Telur/backend/app.py 2>/dev/null', 'main.py / app.py')
r('cat ~/Penetas-Telur/backend/routes.py 2>/dev/null || ls ~/Penetas-Telur/backend/', 'routes / backend ls')
r('ps aux | grep -E "python|flask|uvicorn" | grep -v grep', 'Running processes')
r('cat ~/Penetas-Telur/backend/requirements.txt 2>/dev/null', 'requirements.txt')
r('pip3 list 2>/dev/null | grep -iE "paho|flask|mqtt|gpio"', 'Installed packages (relevant)')
r('systemctl list-units --type=service --state=running 2>/dev/null | grep -v systemd | head -15', 'Running services')
r('cat /etc/systemd/system/*.service 2>/dev/null | head -80', 'Systemd services')

c.close()
print('\nExploration done!', flush=True)
