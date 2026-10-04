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

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[SERVER {lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek WebSocket push thread di Raspi app.py
ras("sed -n '640,720p' ~/Penetas-Telur/backend/app.py", 'Camera push code (640-720)')
ras("grep -n 'camera.*push\|websocket\|ws.*push\|_push_cam\|tunnel_url\|TETASCO_SERVER' ~/Penetas-Telur/backend/app.py | head -15", 'Camera push references')

# Cek apakah ada thread push kamera yang berjalan
ras("python3 -c \"import threading; [print(t.name) for t in threading.enumerate()]\" 2>/dev/null || echo 'cannot check'", 'Running threads (not ideal)')
ras("grep -n '_tunnel_url\\|tunnel_url' ~/Penetas-Telur/backend/app.py | head -10", '_tunnel_url references')

# Server: cek _cam_frames isi
srv("curl -s http://localhost:8000/api/tetasco/1/camera/stats 2>&1 | head -c 300", 'Server camera stats')
srv("docker exec tetasco-backend grep -n '_cam_frames\\|cam_push\\|camera_push' /app/main.py | head -10", 'Server cam_frames')

# Cek apakah WebSocket push aktif dari Raspi
ras("ss -tnp | grep -E '443|8765|websocket' | head -5", 'WebSocket connections')
ras("grep -i 'push\|websocket\|ws.*connect\|camera.*start\|start.*push' /tmp/tetasco_backend.log | tail -10", 'Log push kamera')

rp.close()
sv.close()
