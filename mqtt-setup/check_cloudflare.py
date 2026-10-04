"""check_cloudflare.py — Cek konfigurasi Cloudflare tunnel yang sedang berjalan"""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.14', 22, 'telur', 'telur', timeout=10)

def r(cmd, lbl=''):
    if lbl: print(f'\n[{lbl}]', flush=True)
    i, o, e = c.exec_command(cmd)
    out = o.read().decode('utf-8', 'replace').strip()
    print(out if out else '(empty)', flush=True)
    return out

# Cek container cloudflared detail
r('docker inspect tetasco-cloudflared 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin)[0]; print(\'CMD:\', d[\'Config\'][\'Cmd\']); print(\'ENV:\', [e for e in d[\'Config\'][\'Env\'] if \'TOKEN\' in e or \'TUNNEL\' in e or \'CF\' in e]); print(\'Mounts:\', d[\'Mounts\'])"', 'Cloudflared container config')
r('docker logs tetasco-cloudflared --tail=30 2>&1', 'Cloudflared logs')
r('ls -la ~/.cloudflared/ 2>/dev/null || echo "no ~/.cloudflared dir"', 'cloudflared config dir')
r('find /home/telur -name "*.json" -path "*cloudflare*" 2>/dev/null | head -5', 'Tunnel credential files')
r('find /home/telur -name "config.yml" 2>/dev/null | head -5', 'Config yml files')
r('cat /home/telur/tetasco-connect/cloudflare/config.yml 2>/dev/null', 'Project cloudflare config')

c.close()
print('\nDone!', flush=True)
