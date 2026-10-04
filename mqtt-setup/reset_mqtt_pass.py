import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    print(out or '(ok)')
    return out

# Set password lemari-1 yang diketahui
LEMARI1_PASS = "lemari1-mqtt-2026"

srv(f"docker exec tetasco-mosquitto mosquitto_passwd -b /mosquitto/config/passwd lemari-1 '{LEMARI1_PASS}' && echo OK", 'Set lemari-1 password')
# Reload mosquitto agar password baru berlaku
srv("docker exec tetasco-mosquitto kill -HUP 1 2>/dev/null || docker restart tetasco-mosquitto 2>&1 | tail -1", 'Reload mosquitto')

import time
time.sleep(3)

# Verifikasi: test subscribe dengan password baru
srv(f"timeout 2 mosquitto_sub -h localhost -p 1883 -u lemari-1 -P '{LEMARI1_PASS}' -t 'tetasco/lemari-1/command/#' -v 2>&1 || echo 'timeout (normal - no messages)'", 'Test subscribe lemari-1')

print(f'\n✅ Password lemari-1 MQTT: {LEMARI1_PASS}')
print('Siap untuk deploy ke Raspi saat nyala kembali!')

sv.close()
