"""check_server_api.py — Cek FastAPI main.py di server"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8','replace').strip()
    print(out[:5000] if out else '(empty)', flush=True)

r(f'cat {PROJ}/backend/main.py', 'FastAPI main.py')
c.close()
