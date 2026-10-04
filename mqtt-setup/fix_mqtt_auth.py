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
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

LEMARI1_PASS = 'lemari1-mqtt-2026'

# Config mosquitto di-mount read-only dari HOST → tulis ke HOST
srv('ls -la ~/tetasco-connect/mosquitto/config/', 'Mosquitto config dir')
srv('cat ~/tetasco-connect/mosquitto/config/mosquitto.conf | grep -i read', 'Read-only check di compose')
srv(f"mosquitto_passwd -b ~/tetasco-connect/mosquitto/config/passwd lemari-1 '{LEMARI1_PASS}' && echo OK || echo FAILED", 'Set password di HOST file')

# Reload mosquitto (baca config dari HOST)
srv('docker exec tetasco-mosquitto kill -HUP 1 2>&1 && echo reloaded || docker restart tetasco-mosquitto', 'Reload mosquitto')
time.sleep(4)

# Verifikasi: test subscribe dari dalam container
srv(f"docker exec tetasco-mosquitto mosquitto_sub -h localhost -p 1883 -u lemari-1 -P '{LEMARI1_PASS}' -t 'tetasco/lemari-1/command/#' -C 1 --quiet 2>&1 &", 'Test sub (background)')
time.sleep(1)
srv(f"docker exec tetasco-mosquitto mosquitto_pub -h localhost -p 1883 -u server -P 'srv-7043imRswI0lSdZ3' -t 'tetasco/lemari-1/command/fan' -m '{{\"state\":true,\"ts\":0}}' && echo sent", 'Test pub')
time.sleep(2)

# Raspi: cek MQTT connection sekarang
print('\n[Raspi MQTT log setelah password fix]')
ras('tail -10 /tmp/tetasco_backend.log | grep -i mqtt', 'MQTT log')

# Tunggu reconnect (retry 2 detik)
time.sleep(10)
ras('ss -tnp | grep 1883 | head -3', 'Port 1883 connection')
ras('tail -5 /tmp/tetasco_backend.log', 'App log terbaru')

sv.close()
rp.close()
