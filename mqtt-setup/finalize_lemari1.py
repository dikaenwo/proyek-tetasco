"""finalize_lemari1.py — Install paho-mqtt dan restart backend lemari-1"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '192.168.1.27'
USER = 'tetasco1'
PASS = 'saumata1192'
PROJ = '/home/tetasco1/Penetas-Telur/backend'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASS, timeout=10)
print(f'Connected to {HOST}!', flush=True)

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(120)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8', 'replace')); sys.stdout.flush()
        except: break
    return o.channel.recv_exit_status()

# 1. Install paho-mqtt (Debian PEP 668 → --break-system-packages)
r('pip3 install "paho-mqtt>=2.0.0" --break-system-packages -q && '
  'python3 -c "import paho.mqtt.client as m; print(\'paho-mqtt OK:\', m.__version__)"',
  '1. Install paho-mqtt')

# 2. Verifikasi patch sudah ada di app.py
r(f'grep -c "mqtt_bridge" {PROJ}/app.py && echo "app.py sudah ter-patch"', '2. Cek patch')

# 3. Kill backend lama & restart dengan .env
r('pkill -f "python.*app.py" 2>/dev/null; sleep 2; echo killed', '3. Kill old backend')

r(f'''
cd {PROJ}
set -a; [ -f .env ] && source .env; set +a
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
sleep 5
tail -30 app.log
''', '4. Start backend + log')

c.close()
print('\nDone!', flush=True)
