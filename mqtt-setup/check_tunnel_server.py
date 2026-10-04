import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sv = paramiko.SSHClient()
sv.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sv.connect('tetasco.my.id', 22, 'telur', 'telur', timeout=15)

def r(cmd, lbl='', timeout=15):
    if lbl: print(f'\n[{lbl}]')
    i,o,e = sv.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    print(out or err or '(kosong)')
    return out

# Cek tunnel yang ada
r('which cloudflared 2>/dev/null || which ngrok 2>/dev/null || echo "tunnel tools not in PATH"', '1. Tunnel tools')
r('ps aux | grep -E "cloudflare|ngrok|frp|tunnel" | grep -v grep', '2. Running tunnels')
r('systemctl list-units --state=running 2>/dev/null | grep -E "cloudflare|ngrok|frp|tunnel" || echo "(no systemd tunnel)"', '3. Systemd tunnel services')
r('cat /etc/systemd/system/cloudflared*.service 2>/dev/null || cat ~/.cloudflared/*.json 2>/dev/null || echo "no cloudflared config"', '4. Cloudflared config')
r('cat ~/.ngrok2/ngrok.yml 2>/dev/null || cat ~/ngrok.yml 2>/dev/null || echo "no ngrok config"', '5. Ngrok config')
r('ls -la ~/tunnel* ~/cloudflare* ~/.cloudflared/ 2>/dev/null | head -20 || echo "no tunnel files"', '6. Tunnel files')
r('ls -la /etc/nginx/sites-enabled/ 2>/dev/null && cat /etc/nginx/sites-enabled/* 2>/dev/null | head -60 || echo "no nginx"', '7. Nginx config')
r('hostname -I && curl -s ifconfig.me 2>/dev/null || echo ""', '8. IP addresses')
r('ls ~/Penetas-Telur/ 2>/dev/null || ls ~/ | head -20', '9. Home dir files')

sv.close()
