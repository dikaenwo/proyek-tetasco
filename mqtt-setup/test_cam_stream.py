import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok/empty)')

# Test apakah stream URL server sudah punya frame (camera sudah push)
srv('curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://localhost:8000/api/tetasco/1/camera/stream', 'Stream HTTP status')
srv('curl -s http://localhost:8000/api/tetasco/1/camera/stats', 'Camera stats')
srv('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/tetasco/1/camera/snapshot', 'Snapshot status')

# Cek camera dari luar via Cloudflare
srv('curl -s https://tetasco.my.id/api/tetasco/1/camera/stats', 'Camera stats via Cloudflare')

sv.close()
