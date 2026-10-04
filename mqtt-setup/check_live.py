"""check_live.py — Test koneksi ke tetasco.my.id"""
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

# Cek logs cloudflared terbaru (setelah nginx naik)
r('docker logs tetasco-cloudflared --tail=10 --since=5m 2>&1', 'Cloudflared logs terbaru')

# Test dari server ke service lokal
r('curl -s http://localhost/api/health', 'Local Nginx → FastAPI')
r('curl -s http://localhost:8000/', 'FastAPI langsung')

# Test domain publik dari server
r('curl -sk https://tetasco.my.id/api/health 2>/dev/null || echo "cek dari browser"', 'Public: tetasco.my.id')
r('curl -sk https://api.tetasco.my.id/api/health 2>/dev/null || echo "cek dari browser"', 'Public: api.tetasco.my.id')

# Cek bagaimana cloudflared container dikonfigurasi (token/cmd)
r('docker inspect tetasco-cloudflared --format "{{range .Config.Cmd}}{{.}} {{end}}" 2>/dev/null', 'Container command')
r('docker inspect tetasco-cloudflared --format "{{range .Config.Env}}{{println .}}{{end}}" 2>/dev/null | grep -v PATH', 'Container env')

c.close()
