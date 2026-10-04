"""restart_clean.py"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

r('sudo pkill -9 -f "python.*app.py" 2>/dev/null; sleep 3 && echo killed', 'Kill all')
r('ss -tlnp | grep 5001 || echo port_5001_free', 'Cek port')
r(f'cd {PROJ} && set -a && source .env && set +a && nohup python3 app.py >> app.log 2>&1 & echo "PID:$!"', 'Start')
time.sleep(7)
r(f'tail -20 {PROJ}/app.log', 'Log terbaru')
r('curl -s http://192.168.1.27:5001/api/health', 'API health')
c.close()
print('Done!', flush=True)
