import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('cat ~/Penetas-Telur/dist/kalibrasi.html')
html = o.read().decode('utf-8','replace')

# Fix sisa t_edge di updateStatus
OLD_UPDATE = """    if(d.is_oscillating) {
    const elapsed = (Date.now() - (seqStart||Date.now())) / 1000;
    const t_edge = +document.getElementById('t_edge').value;
    if(elapsed < t_edge) setSeqStep(0);
    else if(elapsed < seqTotal - t_edge) setSeqStep(1);
    else setSeqStep(2);
  }"""

NEW_UPDATE = """    if(d.is_oscillating) {
    const elapsed = (Date.now() - (seqStart||Date.now())) / 1000;
    const t_start = +document.getElementById('t_start').value;
    const t_end   = +document.getElementById('t_end').value;
    if(elapsed < t_start) setSeqStep(0);
    else if(elapsed < seqTotal - t_end) setSeqStep(1);
    else setSeqStep(2);
  }"""

if OLD_UPDATE in html:
    html = html.replace(OLD_UPDATE, NEW_UPDATE, 1)
    print('[OK] updateStatus fixed')
else:
    print('[WARN] updateStatus pattern tidak cocok')

# Verifikasi bersih
sisa = [l.strip() for l in html.split('\n') if 't_edge' in l]
print('[Sisa t_edge]:', sisa if sisa else 'Tidak ada ✅')

sftp = rp.open_sftp()
sftp.putfo(io.BytesIO(html.encode()), '/home/tetasco1/Penetas-Telur/dist/kalibrasi.html')
sftp.close()
print('[OK] HTML diupload')

# Restart Flask
rp.exec_command('pkill -9 -f "app.py" 2>/dev/null')
time.sleep(2)
chan = rp.get_transport().open_session()
chan.exec_command('cd /home/tetasco1/Penetas-Telur && nohup python3 backend/app.py >> /tmp/tetasco_backend.log 2>&1 &')
time.sleep(1); chan.close()
print('[OK] Flask restart')
time.sleep(7)

# Test endpoint
import json
i2,o2,e2 = rp.exec_command('curl -s -X POST http://localhost:5001/api/hydraulic/timed_oscillation -H "Content-Type: application/json" -d \'{"t_start":3.0,"t_end":2.8,"t_down":7.0,"t_up":8.0,"n_cycles":1}\'')
raw = o2.read().decode().strip()
try:
    d = json.loads(raw)
    print(f'[TEST] t_start={d.get("t_start")} t_end={d.get("t_end")} t_down={d.get("t_down")} t_up={d.get("t_up")} total={d.get("total_duration_sec")}s state={d.get("state")}')
except:
    print('[RAW]', raw[:200])

rp.close()
print('\n✅ Selesai! Refresh browser kalibrasi.')
