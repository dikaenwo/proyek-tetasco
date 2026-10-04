import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[RASPI {lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca fungsi camera_push di server
srv('sed -n "482,530p" /home/telur/tetasco-connect/backend/main.py', 'camera_push function')

# Cek URL camera push di Raspi
ras('grep -n "TETASCO_SERVER_WS\|camera/push\|ws://\|wss://\|secret\|RASPI_SECRET\|push_key" ~/Penetas-Telur/backend/app.py | head -15', 'Raspi camera push config')

sv.close()
rp.close()
