"""check_container_path.py — Cek path file di dalam container + tambah debug field"""
import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    o.channel.settimeout(15)
    while True:
        try:
            chunk = o.read(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode('utf-8','replace')); sys.stdout.flush()
        except: break

# 1. Lihat docker inspect volume mapping
r(cs, 'docker inspect tetasco-backend | python3 -c "import json,sys; d=json.load(sys.stdin); [print(m) for m in d[0][\'Mounts\']]"',
  '1. Volume mounts container')

# 2. Cek path main.py di dalam container
r(cs, 'docker exec tetasco-backend find / -name "main.py" -not -path "*/proc/*" 2>/dev/null | head -5',
  '2. main.py path di container')

# 3. Lihat baris 240-245 di dalam container
r(cs, 'docker exec tetasco-backend sed -n "237,247p" /app/main.py 2>/dev/null || docker exec tetasco-backend sed -n "237,247p" /backend/main.py 2>/dev/null || echo "path tidak ketemu"',
  '3. Baris actuators di container main.py')

# 4. Grep actuators di container
r(cs, 'docker exec tetasco-backend grep -n "actuators.*status_cache\|status_cache.*actuators" /app/main.py 2>/dev/null || docker exec tetasco-backend grep -n "actuators" $(docker exec tetasco-backend find / -name main.py 2>/dev/null | head -1) 2>/dev/null | head -5',
  '4. actuators code di container')

cs.close()
print('\nDone!', flush=True)
