import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

i,o,e = rp.exec_command('grep -n "imencode\\|cap\\|CAP_\\|imwrite\\|BUFFERSIZE\\|FOURCC\\|read()\\|retrieve\\|VideoCapture\\|CONVERT" ~/Penetas-Telur/backend/app.py | head -30')
print(o.read().decode('utf-8','replace'))

# Cek format kamera yang didukung
i2,o2,e2 = rp.exec_command('v4l2-ctl -d /dev/video0 --list-formats-ext 2>/dev/null | head -30')
print(o2.read().decode('utf-8','replace'))

rp.close()
