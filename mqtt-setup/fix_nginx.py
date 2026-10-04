"""fix_nginx.py — Diagnosa + fix Nginx 502 ke FastAPI"""
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

# 1. Cek Nginx config
r(cs, 'cat /home/telur/tetasco-connect/nginx/nginx.conf 2>/dev/null || docker exec tetasco-nginx cat /etc/nginx/conf.d/default.conf 2>/dev/null || docker exec tetasco-nginx cat /etc/nginx/nginx.conf',
  '1. Nginx config saat ini')

# 2. Cek docker network - IP container backend
r(cs, 'docker inspect tetasco-backend | python3 -c "import json,sys; d=json.load(sys.stdin); [print(k,\":\",v[\"IPAddress\"]) for k,v in d[0][\"NetworkSettings\"][\"Networks\"].items()]"',
  '2. IP container backend')

# 3. Cek apakah backend bisa di-reach dari nginx container
r(cs, 'docker exec tetasco-nginx wget -qO- http://tetasco-backend:8000/api/health 2>&1 || docker exec tetasco-nginx curl -s http://tetasco-backend:8000/api/health 2>&1',
  '3. Reach backend dari nginx container')

# 4. Cek network yang dipakai
r(cs, 'docker network ls && docker network inspect tetasco-connect_default 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); [print(k,\":\",v[\"IPv4Address\"]) for c in d for k,v in d[0].get(\'Containers\',{}).items()]"',
  '4. Docker network containers')

# 5. Lihat Nginx error log
r(cs, 'docker logs tetasco-nginx --since=5m 2>&1 | tail -20', '5. Nginx error logs')

cs.close()
print('\nDone!', flush=True)
