"""check_sensor_payload.py — Cek format payload dari SHT20 + heartbeat log"""
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
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Subscribe ke MQTT dan lihat format payload sensor & status
r(cs, '''timeout 35 docker exec tetasco-mosquitto mosquitto_sub \
  -h localhost -p 1883 -u server -P "srv-7043imRswI0lSdZ3" \
  -t "tetasco/lemari-1/sensor" \
  -t "tetasco/lemari-1/status" \
  -t "tetasco/lemari-1/heartbeat" \
  -v 2>&1 | head -30''', '1. MQTT payload raw dari lemari-1 (35 detik)')

cl.close()
cs.close()
print('\nDone!', flush=True)
