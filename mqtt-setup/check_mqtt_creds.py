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

# Cek MQTT credentials untuk Raspi lemari
srv("cat ~/tetasco-connect/.env", '.env file')
srv("cat ~/tetasco-connect/mosquitto/config/mosquitto.conf 2>/dev/null | head -30", 'Mosquitto config')
srv("cat ~/tetasco-connect/mosquitto/config/acl.conf 2>/dev/null", 'ACL config')
# Cek password file
srv("docker exec tetasco-mosquitto cat /mosquitto/config/passwd 2>/dev/null | head -10", 'MQTT passwd')

sv.close()
