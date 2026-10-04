"""force_kill_restart.py — Force kill PID di port 5001, restart bersih"""
import paramiko, sys, time
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

# Kill SEMUA yang pakai port 5001 — SIGKILL langsung
r(cl, '''
echo "=== PID di port 5001 ==="
sudo lsof -ti :5001
echo "=== Killing dengan SIGKILL ==="
sudo kill -9 $(sudo lsof -ti :5001 2>/dev/null) 2>/dev/null && echo "Killed!" || echo "Tidak ada yang di-kill"
echo "=== Kill semua python3 ==="
sudo killall -9 python3 2>/dev/null && echo "All python3 killed" || echo "Tidak ada python3"
sleep 4
echo "=== Port status ==="
ss -tlnp | grep 5001 || echo "Port 5001 BEBAS!"
''', '1. Force kill semua')

# Start backend FRESH
r(cl, f'''
cd {PROJ}
> app.log
set -a && source .env && set +a
echo "Transport: $MQTT_TRANSPORT, Broker: $MQTT_BROKER:$MQTT_PORT"
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
''', '2. Start fresh')

print('\n[Tunggu 18 detik untuk MQTT + sensor...]\n', flush=True)
time.sleep(18)

r(cl, f'cat {PROJ}/app.log | grep -v werkzeug | head -25', '3. App.log (no werkzeug)')

print('\n[Tunggu 12 detik lagi...]\n', flush=True)
time.sleep(12)

r(cl, f'grep "Connected\|Sensor\|MQTTBridge" {PROJ}/app.log | tail -8', '4. MQTT status')
r(cs, 'docker logs tetasco-backend --since=40s 2>&1 | grep -iE "sensor|lemari" | tail -5', '5. Server recv')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '6. Sensor endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
