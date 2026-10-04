"""setup_webcam_stream.py — Cek webcam + tambah endpoint streaming ke backend Flask"""
import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rs = paramiko.SSHClient()
rs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
rs.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = rs.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# 1. Cek webcam
r('ls -la /dev/video* 2>/dev/null || echo "Tidak ada video device"', '1. Video devices')
r('v4l2-ctl --list-devices 2>/dev/null | head -20 || echo "v4l2-ctl tidak ada"', '2. v4l2 device list')

# 2. Cek OpenCV / picamera2
r('python3 -c "import cv2; print(\'OpenCV\', cv2.__version__)" 2>/dev/null || echo "OpenCV tidak ada"', '3. OpenCV')
r('python3 -c "import picamera2; print(\'picamera2 OK\')" 2>/dev/null || echo "picamera2 tidak ada"', '4. picamera2')

# 3. Install OpenCV jika belum ada
r('pip3 install opencv-python-headless 2>/dev/null | tail -1 || pip install opencv-python-headless 2>/dev/null | tail -1', '5. Install OpenCV (jika perlu)', timeout=120)

# 4. Cek app.py untuk endpoint kamera yang sudah ada
r('grep -n "camera\|video\|stream\|cv2\|mjpeg\|MJPEG" ~/Penetas-Telur/backend/app.py | head -15', '6. Existing camera endpoints')

rs.close()
print('\n✅ Done diagnosa!')
