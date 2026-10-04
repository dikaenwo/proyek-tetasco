import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rp = paramiko.SSHClient()
rp.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rp.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def ras(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rp.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek video device mana yang capture (bukan metadata)
ras('v4l2-ctl --list-devices 2>/dev/null || echo "v4l2-ctl tidak tersedia"', 'v4l2 devices')
ras('v4l2-ctl -d /dev/video0 --all 2>/dev/null | head -5', 'video0 info')
ras('v4l2-ctl -d /dev/video1 --all 2>/dev/null | head -5', 'video1 info')

# Cek kode camera di app.py
ras('grep -n "video\|CAMERA\|camera_hub\|CameraHub\|video0\|video1\|CAP_V4L" ~/Penetas-Telur/backend/app.py | head -20', 'Camera config in app.py')
ras('grep -rn "video0\|video1\|CAMERA_DEVICE\|camera_device" ~/Penetas-Telur/backend/ | grep -v __pycache__ | head -20', 'Camera device refs')

# Cek server WebSocket endpoint
ras('curl -s https://tetasco.my.id/api/tetasco/1/camera/push -H "Upgrade: websocket" -o /dev/null -w "%{http_code}" 2>/dev/null', 'Server camera WS status')

rp.close()
