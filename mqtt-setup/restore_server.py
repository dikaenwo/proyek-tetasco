import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek ukuran backup
srv('wc -l /home/telur/tetasco-connect/backend/main.py.backup /home/telur/tetasco-connect/backend/main.py_backup 2>/dev/null', 'Backup sizes')
srv('ls -la /home/telur/tetasco-connect/backend/main.py* 2>/dev/null', 'File timestamps')

# Pakai backup yang lebih besar/terbaru
i,o,e = sv.exec_command('wc -c /home/telur/tetasco-connect/backend/main.py.backup /home/telur/tetasco-connect/backend/main.py_backup 2>/dev/null')
sizes = o.read().decode().strip()
print('[sizes]', sizes)

# Restore dari main.py_backup (kemungkinan lebih baru)
srv('cp /home/telur/tetasco-connect/backend/main.py_backup /home/telur/tetasco-connect/backend/main.py && echo OK', 'Restore main.py_backup')
srv('wc -l /home/telur/tetasco-connect/backend/main.py', 'Restored size')
srv('python3 -m py_compile /home/telur/tetasco-connect/backend/main.py && echo SYNTAX_OK || echo SYNTAX_ERROR', 'Syntax check')

# Deploy ke container dan restart
srv('docker cp /home/telur/tetasco-connect/backend/main.py tetasco-backend:/app/main.py && echo ok', 'Deploy to container')
srv('docker restart tetasco-backend 2>&1 | tail -1', 'Restart server', t=25)
time.sleep(15)
srv('docker logs tetasco-backend --tail 10 2>&1', 'Server logs after restart')
srv('curl -s http://localhost:8000/api/health', 'Health check')

sv.close()
