import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cek server
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def rs(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER: {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(kosong)')
    return out

# Cek Raspi
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def rr(cmd, lbl='', t=15):
    if lbl: print(f'\n[RASPI: {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(kosong)')
    return out

# == SERVER ==
rs('curl -s http://localhost:8000/api/tetasco/1/sensor', 'Sensor endpoint')
rs('curl -s http://localhost:8000/api/tetasco/1/status', 'Device status endpoint')
rs('docker exec tetasco-mosquitto mosquitto_sub -h localhost -p 1883 -u server -P "$MQTT_SERVER_PASS" -t "tetasco/+/sensor" -C 1 -W 3 2>/dev/null || echo "no MQTT msg in 3s"', 'MQTT sensor message', t=10)
rs('docker exec tetasco-mosquitto mosquitto_sub -h localhost -p 1883 -u server -P "$MQTT_SERVER_PASS" -t "tetasco/+/heartbeat" -C 1 -W 3 2>/dev/null || echo "no heartbeat in 3s"', 'MQTT heartbeat', t=10)

# == RASPI ==
rr('ps aux | grep app.py | grep -v grep', 'app.py running?')
rr('systemctl is-active tetasco 2>/dev/null || echo "no systemd service"', 'systemd service')
rr('journalctl -u tetasco -n 20 --no-pager 2>/dev/null || tail -20 ~/Penetas-Telur/backend/app.log 2>/dev/null || echo "no log"', 'Recent logs', t=10)

sv.close()
rp.close()
