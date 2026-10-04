import paramiko, sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=15)

def srv(cmd, lbl='', t=10):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=t)
    print(o.read().decode('utf-8','replace').strip() or '(ok)')

# Cek nginx config
srv('find /home/telur -name "nginx.conf" -o -name "*.conf" 2>/dev/null | head -10', 'Find nginx configs')
srv('cat /home/telur/tetasco-connect/nginx.conf 2>/dev/null || cat /etc/nginx/nginx.conf 2>/dev/null | head -50', 'nginx.conf')
srv('docker exec $(docker ps -q --filter name=nginx) cat /etc/nginx/nginx.conf 2>/dev/null | head -60 || echo "no nginx container"', 'nginx container conf')
srv('docker ps', 'All containers')

# Cek docker-compose
srv('cat /home/telur/tetasco-connect/docker-compose.yml 2>/dev/null | head -50', 'docker-compose')

sv.close()
