"""check_cloudflared_status.py — Cek status Cloudflare tunnel running"""
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

# 1. Cek cloudflared running
r(cs, 'docker ps --format "{{.Names}} {{.Status}}" | grep -i cloud; ps aux | grep cloudflared | grep -v grep',
  '1. Cloudflared process')

# 2. Cek route/hostname yang aktif
r(cs, 'docker exec tetasco-cloudflared cloudflared tunnel info 2>/dev/null || cloudflared tunnel list 2>/dev/null || echo "cloudflared tidak di container"',
  '2. Tunnel info')

# 3. Test CORS dari server
r(cs, '''curl -si https://tetasco.my.id/api/health \
    -H "Origin: capacitor://localhost" \
    -H "User-Agent: Mozilla/5.0 Android" | head -15''',
  '3. CORS test dengan Android origin')

# 4. Test dari perspektif Android (header yang WebView kirim)
r(cs, '''curl -si https://tetasco.my.id/api/tetasco/1/sensor \
    -H "Origin: capacitor://localhost" \
    -H "User-Agent: Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36" | head -15''',
  '4. Sensor endpoint dengan Android user-agent')

# 5. Check Cloudflare tunnel container logs
r(cs, 'docker logs tetasco-cloudflared --since=5m 2>&1 | tail -15',
  '5. Cloudflare tunnel logs')

cs.close()
print('\nDone!', flush=True)
