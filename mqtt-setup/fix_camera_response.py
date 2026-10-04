import paramiko, sys, io
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

# Baca app.py
i,o,e = rs.exec_command('cat ~/Penetas-Telur/backend/app.py')
app_py = o.read().decode('utf-8', 'replace')

# Fix 1: tambah Response ke import flask
if 'from flask import' in app_py:
    # Cari baris import flask dan tambah Response jika belum ada
    import re
    def add_response(m):
        imports = m.group(1)
        if 'Response' not in imports:
            return m.group(0).rstrip() + ', Response'
        return m.group(0)
    app_py = re.sub(r'(from flask import [^\n]+)', add_response, app_py, count=1)
    print('[OK] Ditambahkan Response ke flask import')

# Fix 2: ganti _time_mod.sleep dengan __import__('time').sleep
app_py = app_py.replace(
    "_time_mod = __import__('time')\n    _time_mod.sleep(0.5)",
    "__import__('time').sleep(0.5)"
)

# Fix 3: tambah import time di _generate_mjpeg
app_py = app_py.replace(
    '    import time as _time\n    _start_camera(0)',
    '    import time as _time\n    _start_camera(0)'
)

# Verifikasi Response sudah ada
flask_import_line = [l for l in app_py.splitlines() if 'from flask import' in l]
print('Flask imports:', flask_import_line[:2])

sftp = rs.open_sftp()
sftp.putfo(io.BytesIO(app_py.encode()), '/home/tetasco1/Penetas-Telur/backend/app.py')
sftp.close()
print('[OK] app.py uploaded')

# Restart backend
import time
rs.exec_command('pkill -9 -f "backend/app.py" 2>/dev/null')
time.sleep(2)
rs.exec_command('bash -lc "cd ~/Penetas-Telur && nohup python3 backend/app.py > /tmp/tetasco_backend.log 2>&1 &"')
time.sleep(7)

r('curl -s http://localhost:5001/api/health | python3 -c "import sys,json;d=json.load(sys.stdin);print(\'OK:\',d[\'status\'])"', '1. Backend health')
r('grep -i "error\|Error" /tmp/tetasco_backend.log | tail -5', '2. Error log')

# Test camera stream (kirim request, tunggu satu frame)
r('''python3 -c "
import urllib.request, time
try:
    req = urllib.request.urlopen('http://localhost:5001/api/camera/stream', timeout=5)
    data = b''
    while len(data) < 1000:
        chunk = req.read(1024)
        if not chunk: break
        data += chunk
    req.close()
    if b'--frame' in data:
        print('STREAM OK! Frame data received ✅')
    else:
        print('Response received but no frame data:', data[:200])
except Exception as e:
    print('Error:', e)
"''', '3. Test stream (satu frame)')

rs.close()
print('\n✅ Buka di browser PC: http://192.168.1.27:5001/camera')
