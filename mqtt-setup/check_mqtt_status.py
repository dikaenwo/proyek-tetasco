import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

ras('pgrep -fa python3 | grep -v pgrep', 'Proses Python')
ras('tail -20 /tmp/tetasco_backend.log | grep -i mqtt', 'MQTT log')
ras('ss -tnp | grep 1883 | head -5', 'MQTT port 1883')

# Test MQTT direct: publish dari server, lihat apakah Raspi terima
print('\n=== Test MQTT subscriber ===')
srv('docker exec tetasco-mosquitto mosquitto_pub -h localhost -u server -P srv-7043imRswI0lSdZ3 -t tetasco/lemari-1/command/fan -m \'{"state":true,"ts":0}\' && echo ok', 'Publish via MQTT langsung')
time.sleep(1)
ras('tail -5 /tmp/tetasco_backend.log', 'Raspi log setelah MQTT publish')

# Timing end-to-end dari server
print('\n=== Timing test ===')
for action in ['on', 'off']:
    t0 = time.time()
    i,o,e = sv.exec_command(f'curl -s -X POST http://localhost:8000/api/tetasco/1/devices/fan/{action}')
    r = o.read().decode('utf-8','replace').strip()
    print(f'Fan {action}: {(time.time()-t0)*1000:.0f}ms')
    time.sleep(0.3)

rp.close()
sv.close()
