"""kill_pid_direct.py — Kill PID 825736 langsung + restart + verifikasi sensor"""
import paramiko, sys, time, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(30)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Cek semua proses python3 yang running
r(cl, 'sudo ps -ef | grep python3 | grep -v grep', '1. Semua proses python3')

# 2. Kill SEMUA PID dari port 5001 secara langsung
r(cl, '''
# Ambil PID dari ss
PIDS=$(sudo ss -tlnp | grep ':5001' | grep -oP 'pid=\K[0-9]+' | sort -u)
echo "PID di port 5001: $PIDS"
for PID in $PIDS; do
    echo "Killing PID $PID..."
    sudo kill -9 $PID
done
# Juga kill semua python3 yang ada
ALL_PYTHON=$(pgrep -u tetasco1 python3)
echo "Python3 PIDs: $ALL_PYTHON"
for PID in $ALL_PYTHON; do
    echo "Killing python3 PID $PID..."
    sudo kill -9 $PID
done
sleep 5
echo "=== Port 5001 setelah kill ==="
ss -tlnp | grep 5001 || echo "PORT BEBAS!"
''', '2. Kill semua PID python3')

# 3. Start backend bersih
r(cl, f'''
cd {PROJ}
> app.log
set -a && source .env && set +a
echo "Config: transport=$MQTT_TRANSPORT broker=$MQTT_BROKER port=$MQTT_PORT"
nohup python3 app.py >> app.log 2>&1 &
PID=$!
echo "Started PID: $PID"
sleep 3
# Pastikan Flask berjalan
ss -tlnp | grep 5001 && echo "Flask OK!" || echo "Flask BELUM START"
''', '3. Start backend')

print('\n[Tunggu 20 detik MQTT + sensor...]\n', flush=True)
time.sleep(20)

# Cek penuh app.log
r(cl, f'cat {PROJ}/app.log | grep -v werkzeug | tail -20', '4. App.log terbaru')

time.sleep(10)
r(cl, f'grep "Connected\|Sensor\|Error" {PROJ}/app.log | tail -10', '5. MQTT status')
r(cs, 'docker logs tetasco-backend --since=40s 2>&1 | grep -iE "sensor|lemari|Sensor" | tail -5', '6. Server sensor')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '7. Sensor API')

cl.close()
cs.close()
print('\nDone!', flush=True)
