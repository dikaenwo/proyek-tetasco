"""fix_cors_nginx.py — Upload nginx.conf tanpa duplicate CORS ke server"""
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

NGINX_CONF = open('nginx/nginx.conf', 'r', encoding='utf-8').read()

# Upload ke server
sftp = cs.open_sftp()
sftp.putfo(io.BytesIO(NGINX_CONF.encode()), '/home/telur/tetasco-connect/nginx/nginx.conf')
print('[OK] nginx.conf di-upload ke server', flush=True)

# docker cp ke container
r(cs, 'docker cp /home/telur/tetasco-connect/nginx/nginx.conf tetasco-nginx:/etc/nginx/nginx.conf && echo "docker cp OK"',
  '1. docker cp ke container')

# Test config
r(cs, 'docker exec tetasco-nginx nginx -t', '2. Test nginx config')

# Reload
r(cs, 'docker exec tetasco-nginx nginx -s reload && echo "Nginx reload OK"', '3. Reload nginx')

import time; time.sleep(2)

# Verify CORS tidak duplikat sekarang
r(cs, '''curl -si https://tetasco.my.id/api/health \
    -H "Origin: capacitor://localhost" | grep -i "access-control"''',
  '4. Cek CORS headers (harus 1x, bukan 2x)')

r(cs, 'curl -s https://tetasco.my.id/api/tetasco/1/sensor 2>&1 | python3 -m json.tool',
  '5. Sensor endpoint via Cloudflare')

sftp.close()
cs.close()
print('\n✅ Done!', flush=True)
