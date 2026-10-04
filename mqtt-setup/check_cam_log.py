import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok/empty)')

ras('grep -i "camera\\|cam\\|video\\|CamPush\\|CameraHub" /tmp/tetasco_backend.log | tail -20', 'Camera logs')
ras('curl -s http://localhost:5001/api/cloud/status', 'Cloud status')
ras('head -60 /tmp/tetasco_backend.log', 'Startup log')

rp.close()
