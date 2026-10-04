import paramiko, sys
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

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek URL push kamera di Raspi
ras('grep -n "camera/push\|ws://\|wss://\|PUSH_URL\|push_url\|CamPush" ~/Penetas-Telur/backend/app.py | head -15', 'Camera push URL')

# Cek server main.py untuk endpoint WebSocket camera
srv('docker exec tetasco-backend grep -n "camera\|websocket\|ws\|push" /app/main.py | head -20', 'Server camera endpoint')

# Cek apakah server punya websocket support
srv('docker exec tetasco-backend pip show websockets fastapi 2>/dev/null | grep -E "Name|Version"', 'Server WS libs')

# Cek log server untuk error
srv('docker logs tetasco-backend --tail 30 2>&1 | tail -20', 'Server recent logs')

rp.close()
sv.close()
