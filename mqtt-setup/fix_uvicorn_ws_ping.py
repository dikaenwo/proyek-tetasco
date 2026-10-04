import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def srv(cmd, lbl='', t=20):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Baca docker-compose.yml
i,o,e = sv.exec_command('cat /home/telur/tetasco-connect/docker-compose.yml')
dc = o.read().decode('utf-8','replace')

# Tambah command override ke backend service (--ws-ping-interval 0 = nonaktifkan WS ping)
OLD_BACKEND = '''  backend:
    build: ./backend
    container_name: tetasco-backend
    restart: unless-stopped'''

NEW_BACKEND = '''  backend:
    build: ./backend
    container_name: tetasco-backend
    restart: unless-stopped
    # --ws-ping-interval 0: nonaktifkan uvicorn WebSocket ping
    # Default 20s ping + 20s timeout = 40s disconnect kalau client tidak reply pong
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --ws-ping-interval 0'''

if OLD_BACKEND in dc:
    dc = dc.replace(OLD_BACKEND, NEW_BACKEND, 1)
    print('[OK] command override ditambah ke docker-compose.yml')
else:
    print('[WARN] Pattern tidak cocok, cek...')
    print(dc[:500])

sftp = sv.open_sftp()
sftp.putfo(io.BytesIO(dc.encode()), '/home/telur/tetasco-connect/docker-compose.yml')
sftp.close()
print('[OK] docker-compose.yml diupdate')

# Recreate container dengan command baru (tanpa rebuild image)
srv('cd /home/telur/tetasco-connect && docker compose up -d --no-build tetasco-backend 2>&1', 'Recreate container', t=30)
time.sleep(10)

srv('docker logs tetasco-backend --tail 8 2>&1', 'Server logs')
srv('curl -s http://localhost:8000/api/health', 'Health check')

sv.close()
print('\n✅ Uvicorn WS ping dinonaktifkan — broken pipe tiap 40s harusnya hilang!')
