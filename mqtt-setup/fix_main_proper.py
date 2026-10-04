"""fix_main_proper.py — Fix main.py dari file host (bukan container yang crash)"""
import paramiko, sys, io, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cs = paramiko.SSHClient()
cs.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cs.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(c, cmd, lbl='', timeout=30):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8', 'replace')
    err = e.read().decode('utf-8', 'replace')
    sys.stdout.write(out or err); sys.stdout.flush()
    return out

# 1. Cek status container
r(cs, 'docker ps -a --format "{{.Names}} {{.Status}}"', '1. Container status')

# 2. Ambil main.py dari HOST (backup)
r(cs, 'ls -la /home/telur/tetasco-connect/backend/', '2. Host backend folder')
i, o, e = cs.exec_command('cat /home/telur/tetasco-connect/backend/main.py')
content = o.read().decode('utf-8', 'replace')
print(f'[INFO] Host main.py: {len(content)} chars', flush=True)

if not content.strip():
    # Coba dari backup
    i, o, e = cs.exec_command('cat /home/telur/tetasco-connect/backend/main.py_backup')
    content = o.read().decode('utf-8', 'replace')
    print(f'[INFO] Backup main.py: {len(content)} chars', flush=True)

if not content.strip():
    print('[ERROR] main.py kosong! Coba ambil dari container log atau image', flush=True)
    r(cs, 'docker logs tetasco-backend 2>&1 | head -30', 'Container logs')
    sys.exit(1)

# 3. Fix imports
print('\n--- Baris FastAPI import sekarang ---', flush=True)
for i, line in enumerate(content.split('\n')[:20]):
    if 'fastapi' in line.lower() or 'from fastapi' in line:
        print(f'  Line {i+1}: {line}')

# Tambah Request jika belum ada
if 'from fastapi import' in content and 'Request' not in content:
    # Cari baris import FastAPI dan tambah Request
    def add_request(m):
        s = m.group(0)
        if 'Request' not in s:
            s = s.rstrip(')')
            s = s + ', Request)'
        return s
    content = re.sub(r'from fastapi import [^\n]+', add_request, content, count=1)
    print('[FIX] Tambah Request ke import FastAPI', flush=True)
elif 'Request' in content:
    print('[OK] Request sudah ada di import', flush=True)
else:
    # Tambah import manual
    content = 'from fastapi import Request\n' + content
    print('[FIX] Tambah baris import Request', flush=True)

# 4. Fix hmac.new → hmac.new (Python 3 OK)
# Fix jika ada syntax lain
content = content.replace('hmac.new(', 'hmac.new(')  # no-op check

# 5. Pastikan 'import os' ada
if 'import os' not in content:
    content = 'import os\n' + content
    print('[FIX] Tambah import os', flush=True)

# 6. Tulis ke host + docker cp + restart
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(content.encode()), '/home/telur/tetasco-connect/backend/main.py')
sftp.close()
print('[OK] Tulis main.py ke host', flush=True)

r(cs, 'docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo "cp OK"',
  '3. docker cp ke container')

# Stop paksa dulu lalu start
r(cs, 'docker stop tetasco-backend && docker start tetasco-backend && sleep 12', '4. Stop → Start')

# 7. Cek apakah bisa jalan
r(cs, 'docker ps --format "{{.Names}} {{.Status}}" | grep backend', '5. Container status setelah restart')
r(cs, 'docker logs tetasco-backend 2>&1 | tail -10', '6. Container logs')

import time; time.sleep(3)

# 8. Test endpoints
r(cs, 'curl -s http://localhost:8000/api/health', '7. Health check')
r(cs, 'curl -s http://localhost:8000/api/tetasco/1/claim-token | python3 -m json.tool', '8. Claim token endpoint')

cs.close()
print('\n✅ Done!', flush=True)
