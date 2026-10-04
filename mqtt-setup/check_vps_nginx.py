import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    sv.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)
    i,o,e = sv.exec_command('ls -la ~ && find ~/tetasco-server -name "docker-compose.yml" 2>/dev/null || echo "No docker-compose"')
    print("[VPS Home]")
    print(o.read().decode())
    
    i,o,e = sv.exec_command('cat ~/tetasco-server/docker-compose.yml 2>/dev/null || cat ~/tetasco-server/nginx.conf 2>/dev/null || cat ~/tetasco-server/nginx/nginx.conf 2>/dev/null')
    print("\n[Docker/Nginx config]")
    print(o.read().decode())
    sv.close()
except Exception as e:
    print(f"Error: {e}")
