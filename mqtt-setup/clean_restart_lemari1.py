"""clean_restart_lemari1.py — Kill properly + tunggu port bebas + verifikasi sensor"""
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

# Kill ALL processes yang pakai port 5001 atau python3
r(cl, '''
sudo fuser -k 5001/tcp 2>/dev/null
sudo pkill -9 -f "python3.*app.py" 2>/dev/null
sudo pkill -9 -f "python3 app.py" 2>/dev/null
sleep 3
echo "Port 5001 status:"
nc -z 127.0.0.1 5001 && echo "MASIH IN USE!" || echo "FREE - OK!"
''', '1. Kill proses lama + cek port')

# Verify port bebas
r(cl, 'ss -tlnp | grep 5001 || echo "Port 5001 bebas!"', '2. Verify port 5001 bebas')

# Start bersih
r(cl, f'''
cd {PROJ}
> app.log
set -a && source .env && set +a
nohup python3 app.py >> app.log 2>&1 &
echo "PID: $!"
''', '3. Start backend bersih')

print('\n[Tunggu 12 detik untuk MQTT connect...]\n', flush=True)
time.sleep(12)

r(cl, f'grep "MQTTBridge\|MQTT\|Flask\|Serving" {PROJ}/app.log | head -20', '4. App log (MQTT + Flask)')

print('\n[Tunggu 15 detik untuk sensor publish...]\n', flush=True)
time.sleep(15)

r(cl, f'grep "Sensor\|Connected\|MQTTBridge" {PROJ}/app.log | tail -8', '5. Sensor + MQTT status')
r(cs, 'docker logs tetasco-backend --since=30s 2>&1 | grep -iE "sensor|lemari" | tail -5', '6. Server sensor recv')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/sensor', '7. API sensor endpoint')

cl.close()
cs.close()
print('\nDone!', flush=True)
