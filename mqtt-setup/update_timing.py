import paramiko, sys, io, time
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

# ── Raspi: update default values di hydraulic_controller.py ──────────────────
i,o,e = rp.exec_command('cat ~/Penetas-Telur/backend/hardware/hydraulic_controller.py')
ctrl = o.read().decode('utf-8','replace')

ctrl = ctrl.replace(
    'def start_timed_oscillation(\n        self,\n        n_cycles: int = 3,\n        t_center_to_edge: float = 4.0,\n        t_full: float = 9.0,',
    'def start_timed_oscillation(\n        self,\n        n_cycles: int = 3,\n        t_center_to_edge: float = 3.4,\n        t_full: float = 8.3,'
)
print('[Raspi] start_timed_oscillation defaults:', 't_center_to_edge=3.4' in ctrl, 't_full=8.3' in ctrl)

sftp_r = rp.open_sftp()
sftp_r.putfo(io.BytesIO(ctrl.encode()), '/home/tetasco1/Penetas-Telur/backend/hardware/hydraulic_controller.py')
sftp_r.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/hardware/hydraulic_controller.py && echo SYNTAX_OK', 'Syntax Raspi')

# ── Raspi: update default di app.py endpoint ─────────────────────────────────
i2,o2,e2 = rp.exec_command('cat ~/Penetas-Telur/backend/app.py')
app = o2.read().decode('utf-8','replace')

app = app.replace("n_cycles         = int(data.get('n_cycles', 3))\n        t_center_to_edge = float(data.get('t_center_to_edge', 4.0))\n        t_full           = float(data.get('t_full', 9.0))",
                   "n_cycles         = int(data.get('n_cycles', 3))\n        t_center_to_edge = float(data.get('t_center_to_edge', 3.4))\n        t_full           = float(data.get('t_full', 8.3))")
print('[Raspi app.py] defaults:', 't_center_to_edge', 3.4 in [3.4] and '3.4' in app)

sftp_r2 = rp.open_sftp()
sftp_r2.putfo(io.BytesIO(app.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp_r2.close()
ras('python3 -m py_compile ~/Penetas-Telur/backend/app.py && echo SYNTAX_OK', 'Syntax app.py')

# ── Server: update default di main.py ────────────────────────────────────────
i3,o3,e3 = sv.exec_command('docker exec tetasco-backend cat /app/main.py')
main = o3.read().decode('utf-8','replace')

main = main.replace(
    'n_cycles         = int(body.get("n_cycles", 3))\n    t_center_to_edge = float(body.get("t_center_to_edge", 4.0))\n    t_full           = float(body.get("t_full", 9.0))',
    'n_cycles         = int(body.get("n_cycles", 3))\n    t_center_to_edge = float(body.get("t_center_to_edge", 3.4))\n    t_full           = float(body.get("t_full", 8.3))'
)
print('[Server] defaults:', '3.4' in main and '8.3' in main)

sftp_s = sv.open_sftp()
sftp_s.putfo(io.BytesIO(main.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp_s.close()
srv('docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo ok', 'Deploy server')

# ── Restart keduanya ──────────────────────────────────────────────────────────
# Restart Raspi
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
t = rp.get_transport().open_session()
t.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); t.close()
print('[OK] Raspi restart')

# Restart server
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Server restart', t=20)
time.sleep(12)

srv('curl -s http://localhost:8000/api/health', 'Server health')
ras('curl -s http://localhost:5001/api/hydraulic/status', 'Raspi hydraulic status')

print('\n[TEST] Kirim timed_oscillation dengan default baru (3.4 / 8.3):')
ras('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d "{}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'t_edge={d[\\\"t_center_to_edge\\\"]} t_full={d[\\\"t_full\\\"]} total={d[\\\"total_duration_sec\\\"]}s\')"', 'Test defaults Raspi')

rp.close()
sv.close()
print('\n✅ Timing updated: edge=3.4s, full=8.3s')
