import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(conn, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i,o,e = conn.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)'); sys.stdout.flush()
    return out

# ── Fix 1: Restart Docker di server ────────────────────────────────────────
r(sv, 'cd ~/tetasco-connect && docker compose ps', '1. Docker status saat ini')
r(sv, 'cd ~/tetasco-connect && docker compose down && docker compose up -d 2>&1 | tail -10',
  '2. Restart docker compose', timeout=60)
time.sleep(15)
r(sv, 'cd ~/tetasco-connect && docker compose ps', '3. Docker status setelah restart')
r(sv, 'curl -s http://localhost:8000/api/health 2>/dev/null || curl -s http://localhost/api/health 2>/dev/null || echo "not ready"',
  '4. Backend health')
r(sv, 'curl -s "http://localhost:8000/api/tetasco/1/camera/stats" 2>/dev/null || curl -s "http://localhost/api/tetasco/1/camera/stats" 2>/dev/null',
  '5. Camera stats endpoint')

# ── Fix 2: Install websocket-client di Raspi ───────────────────────────────
r(rs, 'pip3 install websocket-client --break-system-packages 2>&1 | tail -3 || pip install websocket-client 2>&1 | tail -3',
  '6. Install websocket-client', timeout=60)
r(rs, 'python3 -c "import websocket; print(\'websocket-client OK:\', websocket.__version__)"', '7. Test import')

# Restart Raspi backend
rs.exec_command('pkill -9 -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(10)
r(rs, 'curl -s http://localhost:5001/api/health | python3 -c "import sys,json;print(json.load(sys.stdin)[\'status\'])"', '8. Raspi backend health')
r(rs, 'grep -E "CamPush|Connected|camera|Error|websocket" /tmp/tetasco_backend.log | tail -10', '9. Raspi cam push log')

sv.close()
rs.close()
print('\n✅ Done!')
