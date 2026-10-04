import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def srv(cmd, lbl='', t=30):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Service name = "backend" (bukan tetasco-backend)
srv('cd /home/telur/tetasco-connect && docker compose up -d --no-build backend 2>&1', 'Recreate backend container', t=30)
time.sleep(12)

srv('docker logs tetasco-backend --tail 5 2>&1', 'Server logs')
srv('docker exec tetasco-backend ps aux | grep uvicorn', 'Uvicorn command check')
srv('curl -s http://localhost:8000/api/health', 'Health')

sv.close()
print('\n✅ Container direcreate dengan --ws-ping-interval 0')
