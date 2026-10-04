"""diagnose.py — Cek kondisi server Tetasco"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/telur/tetasco-connect'

def r(cmd, lbl=''):
    if lbl: print(f'\n{"="*50}\n  {lbl}\n{"="*50}', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    err = e.read().decode('utf-8', 'replace').strip()
    print(out if out else '(empty)', flush=True)
    if err and 'Warning' not in err:
        print(f'STDERR: {err[:500]}', flush=True)
    return out

r('docker ps -a', 'ALL containers (running + stopped)')
r(f'cat {PROJ}/docker-compose.yml', 'docker-compose.yml')
r(f'cd {PROJ} && docker compose logs --tail=50 2>&1', 'Compose logs (last 50)')
r(f'ls -la {PROJ}/mosquitto/config/', 'Mosquitto config')
r(f'wc -l {PROJ}/mosquitto/config/passwd', 'Password file lines')
r(f'cat {PROJ}/.env', '.env content')
r(f'cat {PROJ}/mqtt_passwords.txt', 'MQTT Passwords')
c.close()
print('\nDone!', flush=True)
