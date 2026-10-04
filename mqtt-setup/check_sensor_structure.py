"""check_sensor_structure.py — Cari file sensor_manager yang benar"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect('192.168.1.27', 22, 'tetasco1', 'saumata1192', timeout=10)
PROJ = '/home/tetasco1/Penetas-Telur/backend'

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(20)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

r(cl, f'ls {PROJ}/hardware/', '1. hardware/ folder')
r(cl, f'find {PROJ} -name "sensor*" -o -name "*sensor*" 2>/dev/null | grep -v __pycache__', '2. Sensor files')
r(cl, f'grep -n "def read\|active_sensor_type\|sensor_type\|is_hardware" {PROJ}/hardware/*.py 2>/dev/null | head -20',
  '3. read() signature')

# Test import yang benar langsung dari app.py context
r(cl, f'''timeout 12 python3 << 'PYEOF' 2>&1
import sys, os
os.chdir("{PROJ}")
sys.path.insert(0, "{PROJ}")

# Import seperti app.py melakukannya
exec(open("{PROJ}/app.py").read().split("if __name__")[0].split("from hardware")[0])
print("Trying direct import...")
PYEOF
''', '4. Test via app context')

# Langsung cek sensor_manager.py
r(cl, f'head -80 {PROJ}/hardware/sensor_manager.py 2>/dev/null || echo "File tidak ada"', '5. sensor_manager.py head')

cl.close()
print('\nDone!', flush=True)
