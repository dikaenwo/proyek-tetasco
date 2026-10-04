import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek import _WS di main.py
srv('grep -n "_WS\|WebSocket\|import.*web" /home/telur/tetasco-connect/backend/main.py | head -15', 'WS imports')

# Cek startup error
srv('docker logs tetasco-backend 2>&1 | grep -i "error\|import\|traceback\|exception\|warn" | head -20', 'Startup errors')

# Cek apakah server load routes dengan benar
srv('docker exec tetasco-backend python3 -c "import main; routes=[str(r.path) for r in main.app.routes if hasattr(r,\'path\')]; print([r for r in routes if \'camera\' in r])" 2>&1', 'Camera routes check')

# Test langsung WebSocket ke FastAPI (bypass nginx)
srv('python3 -c "import websocket; ws=websocket.create_connection(\'ws://localhost:8000/api/tetasco/1/camera/push\',timeout=5); print(\'Connected!\'); ws.close()" 2>&1 || echo "FAIL"', 'Direct WS test to FastAPI', t=15)

sv.close()
