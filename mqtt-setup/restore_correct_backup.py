import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Restore dari backup yang BENAR (main.py.backup — 836 baris, Sep 24)
srv('cp /home/telur/tetasco-connect/backend/main.py.backup /home/telur/tetasco-connect/backend/main.py && echo OK', 'Restore main.py.backup')
srv('wc -l /home/telur/tetasco-connect/backend/main.py', 'Restored size')
srv('python3 -m py_compile /home/telur/tetasco-connect/backend/main.py && echo SYNTAX_OK', 'Syntax check')

# Cek endpoint yang ada setelah restore
srv('grep -n "camera/push\|websocket\|@app" /home/telur/tetasco-connect/backend/main.py | head -20', 'Endpoints')

# Cek autentikasi WebSocket camera — kenapa 403
srv('grep -n "403\|Forbidden\|auth\|token\|Authorization\|camera" /home/telur/tetasco-connect/backend/main.py | head -20', 'Auth check')

# Deploy dan restart
srv('docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo ok', 'Deploy')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart', t=25)
time.sleep(15)
srv('curl -s http://localhost:8000/api/health', 'Health')
srv('docker logs tetasco-backend --tail 8 2>&1', 'Logs')

sv.close()
