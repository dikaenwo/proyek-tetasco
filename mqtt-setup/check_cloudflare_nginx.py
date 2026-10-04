"""check_cloudflare_nginx.py — Diagnosa Cloudflare + Nginx frontend"""
import paramiko, sys
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

# 1. Cek Cloudflare tunnel config
r(cs, 'cat /home/telur/tetasco-connect/cloudflare/config.yml 2>/dev/null || cat /home/telur/.cloudflared/config.yml 2>/dev/null || echo "tidak ada config.yml"',
  '1. Cloudflare tunnel config')

# 2. Test API via domain dari server (sama seperti Android)
r(cs, 'curl -sv https://tetasco.my.id/api/health 2>&1 | grep -E "< HTTP|SSL|Connected|health|status" | head -10',
  '2. HTTPS test tetasco.my.id/api/health')

# 3. Cek Nginx HTML folder (apakah kosong?)
r(cs, 'docker exec tetasco-nginx ls -la /usr/share/nginx/html/',
  '3. Nginx HTML folder contents')

# 4. Cek apakah dist punya index.html
r(cs, 'ls -la /home/telur/tetasco-connect/nginx/ 2>/dev/null',
  '4. Nginx folder di host')

# 5. Cek network_security_config Android
r(cs, 'cat /home/telur/tetasco-connect/cloudflare/config.yml 2>/dev/null | head -20',
  '5. Cloudflare config detail')

cs.close()
print('\nDone!', flush=True)
