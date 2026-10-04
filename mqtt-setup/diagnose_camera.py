import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(ok)')

# Cek backend running
ras('pgrep -a python3 | grep app.py', 'Flask running?')
# Cek kamera device
ras('ls -la /dev/video* 2>/dev/null || echo "Tidak ada /dev/video"', 'Video device')
# Cek dmesg kamera
ras('dmesg | grep -i "video\|camera\|uvc" | tail -5', 'dmesg camera')
# Cek log backend
ras('tail -30 /tmp/tetasco_backend.log', 'Backend log')
# Cek apakah ada proses camera push
ras('pgrep -a python3 | grep -i cam', 'Camera process')

rp.close()
