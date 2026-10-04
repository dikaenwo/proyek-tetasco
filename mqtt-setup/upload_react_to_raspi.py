"""upload_react_to_raspi.py — Upload dist/ React SPA terbaru ke Raspi"""
import paramiko, sys, os, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RASPI_IP   = '192.168.1.27'
RASPI_USER = 'tetasco1'
RASPI_PASS = 'saumata1192'
LOCAL_DIST = r'd:\Proyek Penetas Telur\TernakTelur-Cap\dist'
REMOTE_DIR = '/home/tetasco1/Penetas-Telur/dist'

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect(RASPI_IP, 22, RASPI_USER, RASPI_PASS, timeout=10)

def r(c, cmd, lbl='', timeout=20):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    sys.stdout.write(out + '\n' if out else ''); sys.stdout.flush()
    return out

sftp = rs.open_sftp()

def upload_dir(local, remote):
    """Rekursif upload directory."""
    try:
        sftp.stat(remote)
    except FileNotFoundError:
        sftp.mkdir(remote)

    for item in os.listdir(local):
        lpath = os.path.join(local, item)
        rpath = remote + '/' + item
        if os.path.isdir(lpath):
            upload_dir(lpath, rpath)
        else:
            sftp.put(lpath, rpath)
            sys.stdout.write(f'  ↑ {item}\n'); sys.stdout.flush()

print(f'[Upload] {LOCAL_DIST} → {REMOTE_DIR}', flush=True)
upload_dir(LOCAL_DIST, REMOTE_DIR)
sftp.close()
print('[OK] Upload selesai!', flush=True)

# Restart backend agar serve dist/ terbaru
r(rs, 'pkill -9 -f "backend/app.py" 2>/dev/null; echo killed', 'Kill backend')
time.sleep(2)
rs.exec_command('cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &')
time.sleep(5)
r(rs, 'curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(\"Backend OK:\",d.get(\'status\'))"',
  'Backend health')

# Force Chromium buka ulang ke / agar load JS terbaru (dengan watcher fix)
print('\n[Reload Chromium ke dashboard terbaru...]', flush=True)
rs.exec_command('bash ~/redirect_chromium.sh http://127.0.0.1:5001/ >> /tmp/chromium_redirect.log 2>&1 &')
time.sleep(3)
r(rs, 'cat /tmp/chromium_redirect.log 2>/dev/null || echo "log kosong"', 'Redirect log')

rs.close()
print('\n✅ Done! LCD sekarang load React app terbaru (hostname check sudah dihapus)', flush=True)
print('   Hapus lemari di HP → tunggu maks 35 detik → LCD otomatis balik ke /pair', flush=True)
