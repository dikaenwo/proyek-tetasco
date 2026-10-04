"""restart_raspi_backend.py — Restart backend Raspi dan test endpoint baru"""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace')
    err = e.read().decode('utf-8','replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# Cek isi app.py (pairing endpoint sudah masuk?)
r(rs, 'grep -n "pairing-info\\|pair\\|mark-claimed\\|claim-status" ~/Penetas-Telur/backend/app.py | head -10',
  '1. Cek pairing endpoints di app.py')

# Cek startup script
r(rs, 'cat ~/Penetas-Telur/scripts/start_tetasco.sh', '2. Startup script')

# Kill + restart via startup script atau langsung
r(rs, 'pkill -f "app.py" 2>/dev/null; echo killed', '3. Kill old app')
time.sleep(2)

# Start ulang
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/raspi_app.log 2>&1 &')
print('[OK] Backend started', flush=True)
time.sleep(5)

# Test
r(rs, 'curl -s http://localhost:5001/api/pairing-info', '4. Test pairing-info')
r(rs, 'curl -s http://localhost:5001/api/claim-status', '5. Test claim-status')
r(rs, 'curl -si http://localhost:5001/pair 2>&1 | head -8', '6. Test /pair page')
r(rs, 'tail -5 /tmp/raspi_app.log', '7. App log')

rs.close()
print('\n✅ Done!', flush=True)
