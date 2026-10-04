import paramiko, sys, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek Dockerfile — cari CMD/ENTRYPOINT uvicorn
srv('cat /home/telur/tetasco-connect/backend/Dockerfile', 'Dockerfile')

# Cek docker-compose command override
srv('grep -A3 "backend:\|command:" /home/telur/tetasco-connect/docker-compose.yml | head -20', 'docker-compose command')

sv.close()
