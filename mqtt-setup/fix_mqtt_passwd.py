import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')
    return out

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

PASS = 'lemari1-mqtt-2026'

# Trick: copy passwd ke /tmp di container (writable), update, copy balik ke host
print('=== Fix MQTT password untuk lemari-1 ===')
srv('docker cp ~/tetasco-connect/mosquitto/config/passwd tetasco-mosquitto:/tmp/passwd && echo ok', 'Copy passwd ke container /tmp')
srv(f"docker exec tetasco-mosquitto mosquitto_passwd -b /tmp/passwd lemari-1 '{PASS}' && echo ok", 'Set password di /tmp/passwd')
srv('docker cp tetasco-mosquitto:/tmp/passwd ~/tetasco-connect/mosquitto/config/passwd && echo ok', 'Copy balik ke host')
srv('ls -la ~/tetasco-connect/mosquitto/config/passwd', 'Verify file')
# Reload mosquitto
srv('docker exec tetasco-mosquitto kill -HUP 1 2>/dev/null && echo reloaded', 'Reload mosquitto')
time.sleep(3)

# Test login
result = srv(f"timeout 3 docker exec tetasco-mosquitto mosquitto_sub -h localhost -u lemari-1 -P '{PASS}' -t 'tetasco/lemari-1/command/#' -C 1 2>&1 || echo timeout_ok", 'Test login lemari-1')
if 'Connection Refused' in result or 'error' in result.lower():
    print('❌ Login masih gagal')
else:
    print('✅ Login berhasil!')

# Raspi sudah retry setiap 5 detik → tunggu reconnect
print('\nTunggu Raspi reconnect MQTT (5 detik)...')
time.sleep(10)
ras('ss -tnp | grep 1883 | head -3', 'Port 1883 connected')
ras('tail -8 /tmp/tetasco_backend.log | grep -i mqtt', 'MQTT log Raspi')

# Test instant control via MQTT
print('\n=== Test MQTT instant control ===')
time.sleep(3)
srv(f"docker exec tetasco-mosquitto mosquitto_pub -h localhost -u server -P 'srv-7043imRswI0lSdZ3' -t 'tetasco/lemari-1/command/fan' -m '{{\"state\":true,\"ts\":0}}' && echo sent", 'MQTT publish fan ON')
time.sleep(1)
ras('tail -3 /tmp/tetasco_backend.log', 'Raspi log (cek MQTT-Cmd INSTANT)')

sv.close()
rp.close()
print('\nDone!')
