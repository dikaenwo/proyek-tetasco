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

# Cek error
r('curl -s http://localhost:5001/api/camera/stream 2>/dev/null | head -50', '1. Error response body')
r('grep -i "camera\|cv2\|Error\|Traceback\|500" /tmp/tetasco_backend.log | tail -20', '2. Log error')

# Test import cv2 secara manual di konteks backend
r('''python3 -c "
import cv2, threading
cam_frame = None
cam_lock = threading.Lock()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
ret, frame = cap.read()
print('Read frame:', ret, frame.shape if ret else 'None')
if ret:
    ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    print('Encode OK:', ok, 'Size:', len(buf.tobytes()), 'bytes')
cap.release()
"''', '3. Test capture+encode')

rs.close()
